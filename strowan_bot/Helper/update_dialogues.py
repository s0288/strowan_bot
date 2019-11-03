import sys #required because files in other folder
sys.path.append('../Handler/')
from dialogue_bot import DialogueBot

DialogueBot = DialogueBot()
DialogueBot.setup()
