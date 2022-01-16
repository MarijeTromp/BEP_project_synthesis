import time
from typing import Iterator, List, Union

from common.experiment import Example
from common.prorgam import Program
from common.tokens.control_tokens import LoopIterationLimitReached
from common.tokens.pixel_tokens import *
from search.a_star.unique_priority_queue import UniquePriorityQueue
from search.abstract_search import SearchAlgorithm
from search.invent import invent2, invent3, invent4
from search.search_result import SearchResult

MAX_TOKEN_FUNCTION_DEPTH = 3


class AStar(SearchAlgorithm):
    def __init__(self, time_limit_sec: float, weight: Union[int, str] = False, heuristic_override=False, distance_override=False):
        super().__init__(time_limit_sec)
        if weight is False:
            weight = 0.5
        if isinstance(weight, int):
            assert 0 <= weight <= 1
        self.dynamic_weight = False
        if isinstance(weight, str):
            assert weight == 'dynamic'
            self.dynamic_weight = True
        self.weight = weight
        self.heuristic_override = heuristic_override
        self.distance_override = distance_override

    @property
    def best_program(self) -> Program:
        return self._find_program(self._best_program_node, self.reached)

    @property
    def best_f_program(self) -> Program:
        return self._find_program(self._best_f_program_node, self.reached)

    def setup(self, training_examples: List[Example], trans_tokens: set[Token], bool_tokens: set[Token]):
        self.loss_function = self._loss_function
        self.heuristic = self._heuristic_max
        if self.heuristic_override == 'sum':
            self.heuristic = self._heuristic_sum
        elif self.heuristic_override == 'mean':
            self.heuristic = self._heuristic_mean
        elif self.heuristic_override == 'min':
            self.heuristic = self._heuristic_min
        elif self.heuristic_override == 'max':
            self.heuristic = self._heuristic_max

        self.input_envs: tuple[Environment] = tuple(e.input_environment for e in training_examples)
        self.output_envs: tuple[Environment] = tuple(e.output_environment for e in training_examples)
        self.tokens: list[Token] = invent2(trans_tokens, bool_tokens, MAX_TOKEN_FUNCTION_DEPTH)
        # print("\n".join([str(t) for t in self.tokens]))
        # print(f"amount of tokens: {len(self.tokens)}")
        self.number_of_iterations: int = 0
        self.start_time = False
        self._best_cost = float('inf')
        self._best_f_cost = float('inf')
        self.reached = {}
        self._solution_found = False
        self._best_program_node = None
        self._best_f_program_node = None
        self.g_cost_per_iteration = []   # (iteration_number, g_cost)
        self.cost_per_iteration = []  # (iteration_number, h_cost)
        self.program_generator: Iterator[Union[Program, None]] = self.best_first_search_upq(
            self.input_envs, self.output_envs, self.tokens, self.loss_function, self.heuristic)

    def iteration(self, training_example: List[Example], trans_tokens: set[Token], bool_tokens: set[Token]) -> bool:
        if self.dynamic_weight:
            if not self.start_time:
                self.start_time = time.process_time()
            self.weight = 1.0 - max(0.0, (time.process_time() - self.start_time)/self.time_limit_sec)
            self.weight = self.weight * 0.5
        try:
            if node := next(self.program_generator):
                # a solution was found: stop iterating
                self._solution_found = True
                return False
            # no solution found yet: continue iterating
            return True
        except StopIteration:
            # nothing left to explore: stop iterating (will never happen)
            return False

    def extend_result(self, search_result: SearchResult):
        search_result.dictionary['solution_found'] = self._solution_found
        search_result.dictionary['best_f_program'] = str(self.best_f_program)
        search_result.dictionary['g_cost_per_iteration'] = self.g_cost_per_iteration
        search_result.dictionary['heuristic'] = self.heuristic.__name__
        search_result.dictionary['weight'] = self.weight
        return search_result

    @staticmethod
    def _correct(from_states: tuple[Environment], to_states: tuple[Environment]) -> bool:
        return all(map(lambda tup: tup[0].correct(tup[1]), zip(from_states, to_states)))

    def _loss_function(self, g, h):
        return self.weight * g + (1 - self.weight) * h

    @staticmethod
    def _heuristic_mean(from_states: tuple[Environment], to_states: tuple[Environment], distance_override=False) -> float:
        return sum(map(lambda tup: tup[0].distance(tup[1], override=distance_override), zip(from_states, to_states))) / len(from_states)

    @staticmethod
    def _heuristic_min(from_states: tuple[Environment], to_states: tuple[Environment], distance_override=False) -> float:
        return min(map(lambda tup: tup[0].distance(tup[1], override=distance_override), zip(from_states, to_states)))

    @staticmethod
    def _heuristic_max(from_states: tuple[Environment], to_states: tuple[Environment], distance_override=False) -> float:
        return max(map(lambda tup: tup[0].distance(tup[1], override=distance_override), zip(from_states, to_states)))

    @staticmethod
    def _heuristic_sum(from_states: tuple[Environment], to_states: tuple[Environment], distance_override=False) -> float:
        return sum(map(lambda tup: tup[0].distance(tup[1], override=distance_override), zip(from_states, to_states)))

    @staticmethod
    def _find_program(node, reached):
        if node is None:
            return Program([])
        sequence = []
        while reached[node][1]:
            sequence.append(reached[node][2])
            node = reached[node][1]
        sequence.reverse()
        return Program(sequence)

    def save_node_stats(self, node, fcost, gcost, hcost):
        self.cost_per_iteration.append((self.number_of_iterations, hcost))
        self.g_cost_per_iteration.append((self.number_of_iterations, gcost))
        if hcost < self._best_cost:
            self._best_cost = hcost
            self._best_program_node = node
        if fcost < self._best_f_cost:
            self._best_f_cost = fcost
            self._best_f_program_node = node
        self.number_of_iterations += 1
        self.number_of_explored_programs += 1

    def best_first_search_upq(self, start_node: tuple[Environment], end_node: tuple[Environment],
                              tokens: list[Token], f, h) -> Iterator[Program]:
        self.reached = {start_node: (0, False, False)}  # for each reached node: (path_cost, previous_node, token_used)
        queue = UniquePriorityQueue()
        gcost = 0
        hcost = h(start_node, end_node, self.distance_override)
        fcost = f(gcost, hcost)
        queue.insert(start_node, fcost, hcost)
        self._best_program_node = start_node
        self._best_f_program_node = start_node
        while queue:
            node, fcost, _ = queue.pop()
            gcost, _, _ = self.reached[node]
            hcost = h(node, end_node, self.distance_override)
            self.save_node_stats(node, fcost, gcost, hcost)
            if self._correct(node, end_node):
                self.best_program_node = node
                yield node
            else:
                yield None
            node_copies = [copy.deepcopy(node) for _ in tokens]
            for token, node_copy in zip(tokens, node_copies):
                try:
                    child = tuple(map(token.apply, node_copy))
                    gcost_child = gcost + token.number_of_tokens()
                    # if child was not yet expanded or our new gcost is the smallest up until now
                    if child not in self.reached or gcost_child < self.reached[child][0]:
                        self.reached[child] = gcost_child, node, token
                        hcost_child = h(child, end_node, self.distance_override)
                        fcost_child = f(gcost_child, hcost_child)
                        # If infinite reaching end_node is impossible
                        if hcost_child != float('inf'):
                            # in case of fcost tie: node with smallest hcost goes first
                            queue.insert(child, fcost_child, hcost_child)
                except(InvalidTransition, LoopIterationLimitReached):
                    pass
        return
