import itertools
import json
from heapq import *
from typing import Callable, Generator, Iterator

from common.environment import Environment
from common.experiment import Example
from common.prorgam import Program
from common.tokens.control_tokens import RecursiveCallLimitReached, LoopIterationLimitReached
from common.tokens.pixel_tokens import *
from search.abstract_search import SearchAlgorithm
from search.invent import invent2
from search.search_result import SearchResult

MAX_NUMBER_OF_ITERATIONS = 20
MAX_TOKEN_FUNCTION_DEPTH = 3


class AStar(SearchAlgorithm):
    # _best_program: Program
    # input_envs: tuple[Environment]
    # output_envs: tuple[Environment]
    # tokens: list[Token]
    # loss_function: Callable[[int, int], int]
    # program_generator: Iterator[Program]


    def setup(self, training_examples: List[Example], trans_tokens: set[Token], bool_tokens: set[Token]):
        self.input_envs: tuple[Environment] = tuple(e.input_environment for e in training_examples)
        self.output_envs: tuple[Environment] = tuple(e.output_environment for e in training_examples)
        self.tokens: list[Token] = invent2(trans_tokens, bool_tokens, MAX_TOKEN_FUNCTION_DEPTH)
        self.loss_function: Callable[[int, int], int] = lambda g, h: g + h
        self.program_generator: Iterator[Program] = self.best_first_search(self.input_envs, self.output_envs, self.tokens, self.loss_function, self._heuristic_min)
        self._best_program = Program([])
        self._expanded_programs: list[Program] = list()

    def iteration(self, training_example: List[Example], trans_tokens: set[Token], bool_tokens: set[Token]) -> bool:
        if p := next(self.program_generator):
            self._best_program = p
            return False
        return True

    def extend_result(self, search_result: SearchResult):
        search_result.dictionary['expanded_programs'] = self._expanded_programs
        return search_result

    @staticmethod
    def _correct(from_states: tuple[Environment], to_states: tuple[Environment]) -> bool:
        return all(map(lambda tup: tup[0].correct(tup[1]), zip(from_states, to_states)))

    @staticmethod
    def _heuristic(from_states: tuple[Environment], to_states: tuple[Environment]) -> float:
        return sum(map(lambda tup: tup[0].distance(tup[1]), zip(from_states, to_states)))/len(from_states)

    @staticmethod
    def _heuristic_min(from_states: tuple[Environment], to_states: tuple[Environment]) -> float:
        return min(map(lambda tup: tup[0].distance(tup[1]), zip(from_states, to_states)))

    @staticmethod
    def _find_program(node, reached):
        sequence = []
        while reached[node][1]:
            sequence.append(reached[node][2])
            node = reached[node][1]
        sequence.reverse()
        return Program(sequence)

    def best_first_search(self, start_node: tuple[Environment], end_node: tuple[Environment], tokens: list[Token], f, h) -> Iterator[Program]:
        reached = {start_node: (0, False, False)}  # for each reached node: (path_cost, previous_node, token_used)
        queue = []
        count = itertools.count()
        heappush(queue, (f(0, h(start_node, end_node)), next(count), start_node))
        node = False
        while queue:
            total_cost, _, node = heappop(queue)  # total_cost: the estimated cost for the total path
            path_cost, _, _ = reached[node]  # path_cost: the minimal cost so far for a path to this node
            self._expanded_programs.append(self._find_program(node, reached))
            if self._correct(node, end_node):
                break
            else:
                yield False
            node_copies = [copy.deepcopy(node) for _ in tokens]
            for token, node_copy in zip(tokens, node_copies):
                try:
                    child = tuple(map(token.apply, node_copy))
                    if child not in reached or path_cost + token.number_of_tokens(1) < reached[child][0]:
                        reached[child] = path_cost + token.number_of_tokens(1), node, token
                        heappush(queue, (f(path_cost + token.number_of_tokens(1), h(child, end_node)), next(count), child))
                except(InvalidTransition, RecursiveCallLimitReached, LoopIterationLimitReached) as e:
                    pass
        program = self._find_program(node, reached)
        yield program
