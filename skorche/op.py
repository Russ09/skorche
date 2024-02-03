from .constants import QUEUE_SENTINEL
from .node import Node, NodeType
from .queue import Queue

from typing import Callable, Dict, Tuple

class Op(Node):
    """Op node base class"""
    def __init__(self):
        super().__init__(NodeType.OP)


class SplitOp(Op):

    def __init__(self, predicate_fn: Callable, queue_in: Queue, queue_out_dict: Dict):
        """Op node for splitting a queue based on a predicate function"""

        self.predicate_fn = predicate_fn
        self.queue_in = queue_in
        self.queue_out_dict = queue_out_dict    
        self.shutdown = False

    def handle_op(self):
        """
        Gets task item, evaluates a predicate function, and pushes item
        on to appropriate output queue.
        """
        
        if not self.queue_in.empty():
            task_item = self.queue_in.get()
            self.queue_in.task_done()

            if task_item == QUEUE_SENTINEL:
                # push sentinel to output queues and set shutdown flag
                self.handle_sentinel()
            
            else:
                predicate_value = self.predicate_fn(task_item)
                queue_to_push = self.queue_out_dict[predicate_value]
                queue_to_push.put(task_item)

        return self.shutdown

    def handle_sentinel(self):
        """Push the sentinel to all consumers"""

        for queue_out in self.queue_out_dict.values():
            queue_out.put(QUEUE_SENTINEL)
        
        self.shutdown = True

class MergeOp(Op):

    def __init__(self, queues_in: Tuple[Queue], queue_out: Queue):
        """Op node for merging a number of input queues"""
        self.queues_in = queues_in
        self.queue_out = queue_out
        self.shutdown = False

        # for N input queues, expect N sentinels, but only push sentinel
        # to output when N sentinels have been reached
        self.sentinels_reached = 0
        self.sentinels_expected = len(self.queues_in) 
    
    def handle_op(self):
        """
        Pops a value from any input queue and pushes to the output queue
        """
        for q_in in self.queues_in:
            if not q_in.empty():
                task_item = q_in.get()
                q_in.task_done()

                if task_item == QUEUE_SENTINEL:
                    self.handle_sentinel()

                else:
                    self.queue_out.put(task_item)

        return self.shutdown

    def handle_sentinel(self):
        """if expected number of sentinels have been encountered, push sentinel to output"""

        self.sentinels_reached += 1
        if self.sentinels_reached == self.sentinels_expected:
            self.queue_out.put(QUEUE_SENTINEL)
        
            self.shutdown = True

                
                    