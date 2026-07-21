class WorldModel:
    def tick_world(self):
        self.tick += 1
        self.game_time += 1.0 / 60.0
