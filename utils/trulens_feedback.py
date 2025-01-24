import numpy as np
from trulens.core import Feedback
from trulens.core import Select
from trulens.providers.cortex import Cortex
from snowflake.snowpark import Session

def get_trulens_feedbacks(snowpark_session: Session):
    provider = Cortex(snowpark_session, "llama3.1-8b")

    # Define a groundedness feedback function
    f_groundedness = (
        Feedback(
            provider.groundedness_measure_with_cot_reasons, name="Groundedness"
        )
        .on(Select.RecordCalls.retrieve.rets.collect())
        .on_output()
    )
    # Question/answer relevance between overall question and answer.
    f_answer_relevance = (
        Feedback(provider.relevance_with_cot_reasons, name="Answer Relevance")
        .on_input()
        .on_output()
    )

    f_context_relevance = (
        Feedback(provider.context_relevance, name="Context Relevance")
        .on(Select.RecordCalls.retrieve.args.query)
        .on(Select.RecordCalls.retrieve.rets.collect())
        .aggregate(np.mean)
    )
    feedbacks = [f_groundedness, f_answer_relevance, f_context_relevance]