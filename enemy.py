from entity import Entity


class Enemy(Entity):
    def __init__(self, health, mana, damage):
        if health <= 0 or mana < 0 or damage < 0:
            raise ValueError
        super().__init__(health, mana)
        self.damage = damage
        self.x = None
        self.y = None

    def __eq__(self, other):
        return self.damage == other.damage

    def take_mana(self, mana_potion):
        if mana_potion <= 0:
            raise ValueError
        self._current_mana += mana_potion

    def attack(self, by=None):
        if by is None:
            return self.damage
        else:
            return super().attack(by=by)
