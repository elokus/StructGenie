"""TODO: Add voting results to output object."""

import asyncio

from nest_asyncio import apply

from structgenie.engine.async_engine import AsyncEngine
from structgenie.utils import remove_reasoning


def count_output_values_by_key(outputs: list[dict], key: str) -> list[tuple[dict, int]]:
    options = {}
    for output in outputs:
        if output[key] in options:
            options[output[key]] += 1
        else:
            options[output[key]] = 1
    return [(option, options[option]) for option in options]


def count_outputs(outputs: list[dict]) -> list[tuple[dict, int]]:
    options = {}
    option_index_list = []
    option_index_clean_list = []

    for output in outputs:
        clean_output = remove_reasoning(output.copy())
        if clean_output in option_index_clean_list:
            # get index
            index = option_index_clean_list.index(clean_output)
            options[index] += 1
        else:
            option_index_list.append(output)
            option_index_clean_list.append(clean_output)
            options[option_index_list.index(output)] = 1
    return [(option_index_list[i], options[i]) for i in range(len(option_index_list))]


def rank_outputs(outputs: list[dict]) -> list[tuple[dict, int]]:
    """Ranks outputs by the number of times they appear in the outputs list."""
    return sort_count(count_outputs(outputs))


def rank_outputs_by_key(outputs: list[dict], key: str) -> list[tuple[dict, int]]:
    """Ranks output keys by the number of times they appear in the outputs list."""
    return sort_count(count_output_values_by_key(outputs, key))


def sort_count(tuple_list: list[tuple[dict, int]]) -> list[tuple[dict, int]]:
    """Sorts a list of tuples by the second value in the tuple, in descending order."""
    return sorted(tuple_list, key=lambda x: x[1], reverse=True)


class MajorVoteEngine:

    def __init__(
            self,
            template: str,
            total_votes: int = 10,
            min_votes: int = 2,
            **kwargs):
        self.engine = AsyncEngine.from_template(template, **kwargs)
        self.total_votes = total_votes
        self.min_votes = min_votes
        self.return_votes = kwargs.get("return_votes", False)
        self.debug = kwargs.get("debug", False)

    async def gather_engine_run(self, inputs: dict, **kwargs) -> list[dict]:
        outputs = await asyncio.gather(*[self.engine.run(inputs, **kwargs) for _ in range(self.total_votes)])
        return [output for output in outputs if output]

    def run(self, inputs: dict, **kwargs):
        apply()
        outputs: list[dict] = asyncio.run(self.gather_engine_run(inputs, **kwargs))
        self.callback(f"Outputs: {outputs}")
        return self.evaluate_output(outputs)

    def evaluate_output(self, outputs: list[dict]):
        output_rank = rank_outputs(outputs)
        self.callback(f"Output rank: {output_rank}")
        if output_rank[0][1] >= self.min_votes:
            self.callback(f"Majority vote of {output_rank[0][1]}.")
            return output_rank[0][0]
        else:
            self.callback(f"Majority vote of {output_rank[0][1]} failed. Evaluating by key.")
            return self.evaluate_output_by_key(outputs)

    def evaluate_output_by_key(self, outputs: list[dict]):
        composed_output = {}
        failed_keys = []
        for key in self.engine.output_model.keys():
            output_rank = rank_outputs_by_key(outputs, key)
            if output_rank[0][1] >= self.min_votes:
                self.callback(f"Key {key} has a majority vote of {output_rank[0][1]}.")
                composed_output[key] = output_rank[0][0][key]
            elif key == "reasoning":
                composed_output[key] = output_rank[0][0][key]
            else:
                failed_keys.append(key)
        if failed_keys:
            self.callback(f"Key {failed_keys} failed. Evaluating by lowest likelihood model.")
            self.evaluate_output_by_llm(outputs, failed_keys)
        return composed_output

    def evaluate_output_by_llm(self, outputs: list[dict], failed_keys: list[str]):
        """Evaluate outputs by the lowest likelihood model."""
        return NotImplemented

    def callback(self, msg):
        if self.debug:
            msg = "MajorVoteEngine: " + msg + "\n"
            print(msg)
