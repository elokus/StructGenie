from typing import Union

from structgenie.base import BaseGenerationDriver
from langchain import LLMChain, PromptTemplate
from langchain.chat_models import ChatOpenAI


def load_langchain_llm(model_name: str, **kwargs):
    from langchain.chat_models import ChatOpenAI
    return ChatOpenAI(model_name=model_name, **kwargs)


class LangchainDriver(BaseGenerationDriver):
    """Langchain Driver class"""
    executor: LLMChain = None
    model_name: str = "gpt-3.5-turbo"
    chain_kwargs: dict = {}
    llm_kwargs: dict = {}

    def load_llm(self, model_name: str = None, **kwargs) -> ChatOpenAI:
        model_name = model_name or self.model_name
        llm_kwargs_ = self.llm_kwargs.copy()
        if kwargs:
            llm_kwargs_.update(kwargs)
        return load_langchain_llm(model_name=model_name, **llm_kwargs_)

    @classmethod
    def load_driver(
            cls,
            prompt: Union[PromptTemplate, str],
            model_name: str = None,
            llm_kwargs: dict = None,
            **kwargs):

        cls_ = cls()

        llm_kwargs = llm_kwargs or {}
        llm = cls_.load_llm(model_name=model_name, **llm_kwargs)

        chain_kwargs_ = cls_.chain_kwargs.copy()
        if kwargs:
            chain_kwargs_.update(kwargs)

        if isinstance(prompt, str):
            prompt = PromptTemplate.from_template(prompt)

        cls_.executor = LLMChain(prompt=prompt, llm=llm, **chain_kwargs_)

        return cls_

    def predict(self, **kwargs) -> str:
        return self.executor.predict(**kwargs)


class LangchainDriverExpert(LangchainDriver):
    model_name: str = "gpt-4"


class LangchainDriverBasic(LangchainDriver):
    model_name: str = "gpt-3.5-turbo"


class LangchainDriverLong(LangchainDriver):
    model_name: str = "gpt-3.5-16k"
