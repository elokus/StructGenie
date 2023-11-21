import time
from typing import Union, Tuple, Type

from langchain import LLMChain, PromptTemplate
from langchain.callbacks import get_openai_callback
from langchain.chat_models import ChatOpenAI
from langchain.llms import BaseLLM

from structgenie.base import BaseGenerationDriver


def load_langchain_llm(model_name: str, **kwargs):
    from langchain.chat_models import ChatOpenAI
    return ChatOpenAI(model_name=model_name, **kwargs)


class LangchainDriver(BaseGenerationDriver):
    """Langchain Driver class

    For integrating models compatible with the langchain library.

    Usage:
        from langchain.llms import GooglePalm

        llm = GooglePalm(google_api_key=***)
        driver = LangchainDriver.load_driver(prompt=prompt, llm=llm)
        output = driver.predict()
    """
    executor: LLMChain = None
    llm: BaseLLM = None
    chain_kwargs: dict = {}
    llm_kwargs: dict = {}

    @classmethod
    def load_driver(
            cls,
            prompt: Union[PromptTemplate, str],
            llm: BaseLLM = None,
            llm_cls: Type[BaseLLM] = None,
            llm_kwargs: dict = None,
            **kwargs):

        cls_ = cls()

        llm_kwargs = llm_kwargs or {}
        cls_.llm_kwargs = llm_kwargs
        if llm:
            cls_.llm = llm
        elif llm_cls:
            cls_.llm = llm_cls(**llm_kwargs)
        else:
            raise ValueError("Must provide either llm or llm_cls.")

        chain_kwargs_ = cls_.chain_kwargs.copy()
        if kwargs:
            chain_kwargs_.update(kwargs)

        if isinstance(prompt, str):
            prompt = PromptTemplate.from_template(prompt)

        cls_.executor = LLMChain(prompt=prompt, llm=llm, **chain_kwargs_)

        return cls_

    def predict(self, **kwargs) -> str:
        return self.executor.predict(**kwargs)

    def predict_and_measure(self, **kwargs) -> Tuple[str, dict]:
        with get_openai_callback() as cb:
            exec_start = time.time()
            output = self.executor.predict(**kwargs)
            execution_metrics = {
                "execution_time": time.time() - exec_start,
                "token_usage": cb.total_tokens,
                "model_name": self.llm.model_name if hasattr(self.llm, "model_name") else None,
                "model_config": self.llm_kwargs,
            }
        return output, execution_metrics

    async def predict_async(self, **kwargs) -> str:
        return await self.executor.apredict(**kwargs)

    async def predict_and_measure_async(self, **kwargs) -> Tuple[str, dict]:
        with get_openai_callback() as cb:
            exec_start = time.time()
            output = await self.executor.apredict(**kwargs)
            execution_metrics = {
                "execution_time": time.time() - exec_start,
                "token_usage": cb.total_tokens,
                "model_name": self.model_name,
                "model_config": self.llm_kwargs,
            }
        return output, execution_metrics


class LangchainOpenAIDriver(BaseGenerationDriver):
    """Langchain Driver class"""
    executor: LLMChain = None
    model_name: str = "gpt-3.5-turbo"
    chain_kwargs: dict = {}
    llm_kwargs: dict = {}
    load_llm = load_langchain_llm

    def call_load_llm(self, model_name: str = None, **kwargs) -> ChatOpenAI:
        model_name = model_name or self.model_name
        llm_kwargs_ = self.llm_kwargs.copy()
        if kwargs:
            llm_kwargs_.update(kwargs)
        return self.load_llm(model_name=model_name, **llm_kwargs_)

    @classmethod
    def load_driver(
            cls,
            prompt: Union[PromptTemplate, str],
            model_name: str = None,
            llm_kwargs: dict = None,
            **kwargs):

        cls_ = cls()

        llm_kwargs = llm_kwargs or {}
        llm = cls_.call_load_llm(model_name=model_name, **llm_kwargs)

        chain_kwargs_ = cls_.chain_kwargs.copy()
        if kwargs:
            chain_kwargs_.update(kwargs)

        if isinstance(prompt, str):
            prompt = PromptTemplate.from_template(prompt)

        cls_.executor = LLMChain(prompt=prompt, llm=llm, **chain_kwargs_)

        return cls_

    def predict(self, **kwargs) -> str:
        return self.executor.predict(**kwargs)

    def predict_and_measure(self, **kwargs) -> Tuple[str, dict]:
        with get_openai_callback() as cb:
            exec_start = time.time()
            output = self.executor.predict(**kwargs)
            execution_metrics = {
                "execution_time": time.time() - exec_start,
                "token_usage": cb.total_tokens,
                "model_name": self.model_name,
                "model_config": self.llm_kwargs,
            }
        return output, execution_metrics

    async def predict_async(self, **kwargs) -> str:
        return await self.executor.apredict(**kwargs)

    async def predict_and_measure_async(self, **kwargs) -> Tuple[str, dict]:
        with get_openai_callback() as cb:
            exec_start = time.time()
            output = await self.executor.apredict(**kwargs)
            execution_metrics = {
                "execution_time": time.time() - exec_start,
                "token_usage": cb.total_tokens,
                "model_name": self.model_name,
                "model_config": self.llm_kwargs,
            }
        return output, execution_metrics


class LangchainDriverExpert(LangchainOpenAIDriver):
    model_name: str = "gpt-4"


class LangchainDriverBasic(LangchainOpenAIDriver):
    model_name: str = "gpt-3.5-turbo"


class LangchainDriverLong(LangchainOpenAIDriver):
    model_name: str = "gpt-3.5-16k"
