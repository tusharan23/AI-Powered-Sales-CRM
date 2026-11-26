import os
import pandas as pd

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LEADS_FILE = os.path.join(ROOT_DIR, "CRM_Leads.csv")
TASKS_FILE = os.path.join(ROOT_DIR, "Execution_Tasks.csv")


class CRMLeadsDB:

    columns = [
        "client_name",
        "company",
        "deal_value",
        "deal_stage",
        "technical_requirements",
        "priority",
        "next_action"
    ]

    @classmethod
    def _ensure_file(cls):
        if not os.path.exists(LEADS_FILE):
            pd.DataFrame(columns=cls.columns).to_csv(
                LEADS_FILE,
                index=False
            )

    @classmethod
    def get_all(cls):
        cls._ensure_file()

        df = pd.read_csv(LEADS_FILE)

        return df.to_dict("records")

    @classmethod
    def add(
        cls,
        client_name,
        company,
        deal_value,
        deal_stage,
        technical_requirements,
        priority,
        next_action
    ):
        cls._ensure_file()

        df = pd.read_csv(LEADS_FILE)

        new_row = {
            "client_name": client_name,
            "company": company,
            "deal_value": deal_value,
            "deal_stage": deal_stage,
            "technical_requirements": technical_requirements,
            "priority": priority,
            "next_action": next_action
        }

        df = pd.concat(
            [df, pd.DataFrame([new_row])],
            ignore_index=True
        )

        df.to_csv(
            LEADS_FILE,
            index=False
        )

    @classmethod
    def clear(cls):
        pd.DataFrame(columns=cls.columns).to_csv(
            LEADS_FILE,
            index=False
        )


class ExecutionTasksDB:

    columns = [
        "task_description",
        "assignee",
        "deadline",
        "status",
        "linked_client"
    ]

    @classmethod
    def _ensure_file(cls):
        if not os.path.exists(TASKS_FILE):
            pd.DataFrame(columns=cls.columns).to_csv(
                TASKS_FILE,
                index=False
            )

    @classmethod
    def get_all(cls):
        cls._ensure_file()

        df = pd.read_csv(TASKS_FILE)

        return df.to_dict("records")

    @classmethod
    def add(
        cls,
        task_description,
        assignee,
        deadline,
        status,
        linked_client
    ):

        cls._ensure_file()

        df = pd.read_csv(TASKS_FILE)

        new_row = {
            "task_description": task_description,
            "assignee": assignee,
            "deadline": deadline,
            "status": status,
            "linked_client": linked_client
        }

        df = pd.concat(
            [df, pd.DataFrame([new_row])],
            ignore_index=True
        )

        df.to_csv(
            TASKS_FILE,
            index=False
        )

    @classmethod
    def clear(cls):
        pd.DataFrame(columns=cls.columns).to_csv(
            TASKS_FILE,
            index=False
        )

# ----------------------------------------------------------
# Extra helpers used by the redesigned UI
# (appended so the original classes above stay untouched)
# ----------------------------------------------------------

def _leads_delete(index: int):
    """Delete a lead by its row position."""
    CRMLeadsDB._ensure_file()
    df = pd.read_csv(LEADS_FILE)
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        df.to_csv(LEADS_FILE, index=False)


def _leads_update_stage(index: int, new_stage: str):
    """Change the deal stage of a lead by its row position."""
    CRMLeadsDB._ensure_file()
    df = pd.read_csv(LEADS_FILE)
    if 0 <= index < len(df):
        df.loc[df.index[index], "deal_stage"] = new_stage
        df.to_csv(LEADS_FILE, index=False)


def _tasks_update_status(index: int, new_status: str):
    """Change the status of a task by its row position."""
    ExecutionTasksDB._ensure_file()
    df = pd.read_csv(TASKS_FILE)
    if 0 <= index < len(df):
        df.loc[df.index[index], "status"] = new_status
        df.to_csv(TASKS_FILE, index=False)


def _tasks_delete(index: int):
    ExecutionTasksDB._ensure_file()
    df = pd.read_csv(TASKS_FILE)
    if 0 <= index < len(df):
        df = df.drop(df.index[index]).reset_index(drop=True)
        df.to_csv(TASKS_FILE, index=False)


CRMLeadsDB.delete = staticmethod(_leads_delete)
CRMLeadsDB.update_stage = staticmethod(_leads_update_stage)
ExecutionTasksDB.update_status = staticmethod(_tasks_update_status)
ExecutionTasksDB.delete = staticmethod(_tasks_delete)
