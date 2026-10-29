"""Inspect existing dependencies and private key presence without revealing secrets."""
import importlib.metadata as md
import json
import os
import sys
from pathlib import Path
from provider import load_environment

if __name__=='__main__':
    load_environment()
    info={'python':sys.version,'packages':{}}
    for name in ['pydantic','pytest','openai','mcp']:
        try:info['packages'][name]=md.version(name)
        except md.PackageNotFoundError:info['packages'][name]='NOT INSTALLED'
    info['api_key_present']=bool(os.getenv('DEEPSEEK_API_KEY'))
    info['model']=os.getenv('DEEPSEEK_MODEL','deepseek-flash')
    info['data_present']=(Path(__file__).resolve().parent/'data/engineering.sqlite').exists()
    print(json.dumps(info,indent=2))
