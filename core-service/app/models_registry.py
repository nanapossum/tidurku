# Impor semua modul model konteks di sini agar create_all mengenali tabelnya.
from .identity import models as identity_models  # noqa: F401
from .tracking import models as tracking_models  # noqa: F401
from .goals import models as goals_models  # noqa: F401
from .reminders import models as reminders_models  # noqa: F401
from .environment import models as environment_models  # noqa: F401
