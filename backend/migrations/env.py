import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from app.database import Base
from app import models   # ensure all models are loaded

target_metadata = Base.metadata