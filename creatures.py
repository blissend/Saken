import npc

# TODO: Make unique for creatures, make them do things only they can do
class Creatures(npc.NPC):
    def __init__(self):
        super().__init__()
        self.cmd.npc_table = 'stats_npc_creatures'
        self.cmd.mode = 'creatures'

if __name__ == '__main__':
    pass