import sys
sys.path.insert(0, r'G:\research\01_agents\swe-e2e\Bmk-dev\runs\minidynaconf-realrepo-001\solution-openhands-qwen-001')
from minidynaconf import MiniDynaconf, Validator, ValidationError

settings = MiniDynaconf(
    defaults={'PORT': 8080},
    validators=[Validator('PORT', required=True)]
)
print('Before set:', settings.PORT)
try:
    settings.set('PORT', 'invalid', validate=True)
    print('After set (no error):', settings.PORT)
except ValidationError as e:
    print('ValidationError:', e)
except Exception as e:
    print('Other exception:', type(e), e)