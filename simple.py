import npc

# TODO: Make unique for simple(citizens), make them do things only they can do
class Simple(npc.NPC):
    def __init__(self):
        super().__init__()
        self.cmd.npc_table = 'stats_npc_simple'
        self.cmd.mode = 'simple'

if __name__ == '__main__':
    pass