from datetime import datetime
from typing import Iterator, Union

from agno.agent import Message
from agno.workflow import Workflow
from llmlingua import PromptCompressor

from agents.redactor import build_writer_agent
from tools.rss_feed import BlogCollector


class NewsBlogWorkflow:

    writer = build_writer_agent()

    def __init__(self):
        self.__feed_reader = BlogCollector()


    def add_feed(self, url):
        self.__feed_reader.add_source(url)


    def run(
        self,
        time_limit: Union[int, datetime] = 1
    ):
        news = self.__feed_reader.collect(time_limit=time_limit)

        # Context 
        sources = f"""
        Here are sources from today feeds. Pick some that most fits to your knowledge and interest. Then write a blog 
        article based on your selected sources.

        # SOURCES
        {str(news)}
        """

        # Compress prompt
        llm_lingua = PromptCompressor()
        compressed_prompt = llm_lingua.compress_prompt(
            sources,
            rate=0.55,
            # Set the special parameter for LongLLMLingua
            condition_in_question="after_condition",
            reorder_context="sort",
            dynamic_context_compression_ratio=0.3,
            condition_compare=True,
            context_budget="+100",
            rank_method="longllmlingua",
        )

        return self.writer.run(
            input=[
                Message(role="user", content=compressed_prompt)
            ]
        )
