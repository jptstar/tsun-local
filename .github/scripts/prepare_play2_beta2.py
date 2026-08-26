from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
source = subprocess.check_output(
    ["git", "show", "HEAD^:.github/scripts/prepare_play2_beta2.py"],
    cwd=root,
    text=True,
)
exec(compile(source, "prepare_play2_beta2_impl.py", "exec"))

entities_path = root / "docs/ENTITIES.md"
text = entities_path.read_text(encoding="utf-8")
text = text.replace(
    "**Status:** ✅ Validated on TSOL-MX500 and Sunology PLAY2  \n",
    "**Status:** ✅ Validated on TSOL-MX500 and Sunology PLAY2\n",
    1,
)
entities_path.write_text(text, encoding="utf-8")
