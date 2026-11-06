from enum import Enum

class AgentState(str, Enum):
    STOPPED = "STOPPED"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    RECOVERING = "RECOVERING"
    ERROR = "ERROR"

class PipelineStage(str, Enum):
    IDLE = "IDLE"
    DISCOVER = "DISCOVER"
    RESEARCH = "RESEARCH"
    SCRIPT = "SCRIPT"
    SCENE_PLAN = "SCENE_PLAN"
    RENDER_3D = "RENDER_3D"
    AUDIO_ASSEMBLY = "AUDIO_ASSEMBLY"
    QC = "QC"
    PUBLISH = "PUBLISH"
    COMPLETE = "COMPLETE"
