from random import choice
from treasure import Treasure
import json
from errors import LogicError
from spell import Spell
from weapon import Weapon
from fight import Fight
from enemy import Enemy


class Dungeon:
    spawning_point = 'S'
    gateway = 'G'
    treasure = 'T'
    obstacle = '#'
    path = '.'
    enemy_symbol = 'E'
    hero_symbol = 'H'

    def __init__(self, map_file, treasure_file, enemy_file):
        with open(map_file, 'r') as f:
            self.map = f.readlines()
            self.map = [list(x[:-1]) for x in self.map]
            self.hero = None
        with open(treasure_file, 'r') as f2:
            treasure_dictionary = json.load(f2)
            self.weapons = treasure_dictionary["weapons"]
            self.weapons = [Weapon(**weapon) for weapon in self.weapons]
            self.spells = treasure_dictionary["spells"]
            self.spells = [Spell(**spell) for spell in self.spells]
        with open(enemy_file, 'r') as f3:
            enemy_dictionary = json.load(f3)
            self.enemies = [Enemy(**enemy) for enemy in enemy_dictionary["enemies"]]

    def print_map(self):
        if self.hero is not None:
            if self.hero.x is not None and self.hero.y is not None:
                previous_symbol = self.map[self.hero.y][self.hero.x]
                self.map[self.hero.y][self.hero.x] = self.hero_symbol
                for x in self.map:
                    print("".join(x))
                self.map[self.hero.y][self.hero.x] = previous_symbol
        else:
            for x in self.map:
                print("".join(x))

    def spawn(self, hero):
        self.hero = hero
        for y in range(len(self.map)):
            if self.spawning_point in self.map[y]:
                x = self.map[y].index(self.spawning_point)
                self.hero.x = x
                self.hero.y = y
                self.map[self.hero.y][self.hero.x] = self.path
                self.hero._current_health = hero._max_health
                self.hero._current_mana = hero._max_mana
                return True
        return False

    def pick_up_treasure(self):
        print('WOW!! YOU FOUND A TREASURE! :o')
        treasure = choice(list(Treasure))
        if treasure == Treasure.Weapon:
            weapon = choice(self.weapons)
            print('You received this weapon: ' + str(weapon))
            self.hero.equip(weapon)
        if treasure == Treasure.Spell:
            spell = choice(self.spells)
            print('You received this spell: ' + str(spell))
            self.hero.learn(spell)
        if treasure == Treasure.Health:
            print('You received health potion')
            self.hero.receive_health_potion()
        if treasure == Treasure.Mana:
            print('You received mana potion')
            self.hero.receive_mana_potion()

    def move_hero(self, direction):
        y = self.hero.y
        x = self.hero.x
        if direction == "up":
            self.hero.y -= 1
        elif direction == "down":
            self.hero.y += 1
        elif direction == "right":
            self.hero.x += 1
        elif direction == "left":
            self.hero.x -= 1

        if not 0 <= self.hero.x < len(self.map[0]):
            self.hero.x = x
            self.print_map()
            return False

        if not 0 <= self.hero.y < len(self.map):
            self.hero.y = y
            self.print_map()
            return False

        if self.map[self.hero.y][self.hero.x] == self.obstacle:
            self.hero.x = x
            self.hero.y = y
            self.print_map()
            return False

        if self.map[self.hero.y][self.hero.x] == self.treasure:
            self.pick_up_treasure()
            self.map[self.hero.y][self.hero.x] = self.path

        if self.map[self.hero.y][self.hero.x] == self.enemy_symbol:
            if self.hero.spell is not None and self.hero.weapon is not None:
                first_attack = choice([self.hero.weapon, self.hero.spell])
            else:
                first_attack = self.hero.spell if self.hero.spell else self.hero.weapon
            self.map[self.hero.y][self.hero.x] = self.path
            if self.start_a_fight(self.hero.x, self.hero.y, first_attack):
                self.map[self.hero.y][self.hero.x] = self.enemy_symbol
                if not self.spawn(self.hero):
                    print("End Game!")
                else:
                    print('HERO RESPAWNED!')
            else:
                self.enemies.remove(self.enemy)

        self.hero.take_mana(None)
        self.print_map()
        return True

    def start_a_fight(self, enemy_x, enemy_y, first_attack):
        weapons = self.weapons + [None]
        spells = self.spells + [None]
        weapon = choice(weapons)
        spell = choice(spells)
        self.enemy = choice(self.enemies)
        self.enemy.x = enemy_x
        self.enemy.y = enemy_y
        self.enemy.learn(spell)
        self.enemy.equip(weapon)
        fight = Fight(self.enemy)
        return fight.fight(self.hero, first_attack)

    def can_attack(self, y, x, attack_range):
        for k in range(1, attack_range + 1):
            if not 0 <= self.hero.x + x * k < len(self.map[0]) or not 0 <= self.hero.y < len(self.map):
                return False
            if self.map[self.hero.y + y * k][self.hero.x + x * k] == self.obstacle:
                return False
            if self.map[self.hero.y + y * k][self.hero.x + x * k] == self.enemy_symbol:
                return (self.hero.y + y * k, self.hero.x + x * k)
        return False

    def try_attack(self, attack_range, by):
        x = [-1, 1, 0, 0]
        y = [0, 0, -1, 1]
        for i in range(4):
            attack = self.can_attack(y[i], x[i], attack_range)
            if attack:
                self.map[attack[0]][attack[1]] = self.path
                if self.start_a_fight(attack[1], attack[0], by):
                    self.map[self.enemy.y][self.enemy.x] = self.enemy_symbol
                    if not self.spawn(self.hero):
                        print("End Game!")
                    else:
                        print('HERO RESPAWNED!')
                else:
                    self.enemies.remove(self.enemy)
                break
            # else:
            #   print("Hero can't see an enemy to attack!")
            #  break

    def hero_attack(self, by):
        by = by.lower()
        if by == "weapon":
            if self.hero.weapon is None:
                print("You have no weapon!")
            else:
                self.try_attack(1, self.hero.weapon)
        elif by == "magic":
            if self.hero.spell is None:
                print("You have no spell!")
            else:
                try:
                    if self.hero.can_cast():
                        cast_range = self.hero.spell.cast_range
                        self.try_attack(cast_range, self.hero.spell)
                    else:
                        print('Not in range!')
                except LogicError as err:
                    print(err)
        else:
            print("No such option for by")

    def can_exit(self):
        for y in range(len(self.map)):
            if self.gateway in self.map[y]:
                x = self.map[y].index(self.gateway)
                if self.hero.x == x and self.hero.y == y:
                    for level in self.map:
                        if level.count('E') != 0:
                            print('YOU CANT LEAVE YET! YOU NEED TO KILL ALL ENEMIES!')
                            return False
                    print('YOU LEFT THE DUNGEON. WELL PLAYED!')
                    return True
        return False
