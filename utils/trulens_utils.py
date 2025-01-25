from trulens.apps.custom import TruCustomApp

def get_trulens_recorder(app, app_version, feedbacks):
    tru_recorder = TruCustomApp(
        app = app,
        app_name="RAG",
        app_version=app_version,
        feedbacks= feedbacks
    )
    return tru_recorder