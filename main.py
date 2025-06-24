import random
import ast
from collections import Counter
import sys
import functools
print = functools.partial(print, flush=True)
_original_input = input

_original_input = input
def input(prompt=""):
    while True:
        try:
            return _original_input(prompt)
        except (EOFError, KeyboardInterrupt):
            print("[!] Input failed or was interrupted. Please try again.")

            
VERSION = "14"  # ← change this manually when you update!
print(f"\n🔄 SSRPG Game Version: {VERSION}\n")


# Ohm,200,200, 50, 50,50,5,1,15

# Define constants for status effects and travel outcomes
BLEED_DAMAGE = 5
BURN_DAMAGE = 3
POISON_DAMAGE = 3
RED_BLIGHT_DAMAGE = 8 
DAZE_PROBABILITY = 0.05

BURN_CHANCE = 0.02
BLEED_CHANCE = 0.03
POISON_CHANCE = 0.05
RED_CHANCE = 0.04

BIOME_ABBREVIATIONS = {
    "Howler's Rise": "HR",
    "Whispering Pines": "WP",
    "Cinderglen": "CG",
    "Deadlands": "DL",
    "Blacktide Beach": "BB"
}

PLANT_ABBREVIATIONS = {
    "Dock Leaves": "DL",
    "Goldenrod": "GR",
    "Blackberry Leaves": "BL",
    "Comfrey Root": "CR",
    "Marigold": "MR",
    "Horsetail": "HT",
    "Juniper Berries": "JB",
    "Poppy Seeds": "PS",
    "Burdock Root": "BR",
    "Seaweed": "SW",
    "Grass": "GS",
    "Catmint": "CM",
    "Thistle Patches": "TP"
}

PREY_NAMES = {
    "Sparrow", "Rabbit", "Water Vole", "Small Fish",
    "Mouse", "Squirrel", "Thrush", "Blackbird",
    "Mountain Hare", "Small Bird", "Vole",
    "Trout", "Minnow", "Crab"
}

# === VALUE SYSTEM ===
ITEM_VALUES = {
# === DROPS (~5–20 max) ===
    "Fur": 1, "Feather": 1, "Scale": 3, "Shell": 3, "Bone": 4,
    "Claw": 3, "Tooth": 3, "VenomGland": 9, "RottenMeat": 9, "Hide": 3,

    # === GATHERABLES (~5–15 max) ===
    "Comfrey Root": 6, "Goldenrod": 6, "Horsetail": 8, "BurdockRoot": 6,
    "DockLeaves": 4, "JuniperBerries": 4, "Marigold": 4, "BlackberryLeaves": 3,
    "Catmint": 8, "Grass": 2, "ThistlePatches": 3, "Seaweed": 3, "PoppySeeds": 8,
    "Stick": 2, "Sap": 6, "Moss": 3, "Pinecone": 4, "Rock": 5, "Antler": 12,
    "Root": 5, "Stone": 6,

    # === MEAT ===
    "SmallMeat": 6, "MediumMeat": 12, "LargeMeat": 20,

    # === MEDICINE (100–120) ===
    "BasicHealingPoultice": 100, "WoundSalve": 110, "PoisonCleanser": 115,
    "StaminaTonic": 105, "StrongHealingMixture": 120,

    # === ARMORS / CRAFTED GEAR (150–200) ===
    "FurHood": 150, "FurVest": 160, "FurLegwraps": 150,
    "HideHood": 170, "HideVest": 180, "HideLegwraps": 170,
    "BoneHood": 190, "BoneVest": 200, "BoneLegwraps": 190,
    "SpikedCollar": 180, "DefenseWrap": 170,
    "ForestLuckCharm": 150, "AntlerHood": 160,
    "StonyHideLegwraps": 175,

    # === CRAFTING ITEMS ===
    "Shard": 100,
    "ArmorReinforcementPaste": 99,

    # === STATS (~360) ===
    "+1 Damage": 360, "+1 Stamina": 360, "+1 Health": 360,
    "+1 Luck": 360, "+1 Protection": 360, "+1 Dice Face": 360,
    "+1 Inventory Slot": 360
}

NONSENSE_TASK_ITEMS = {
    "+1 Luck", "+1 Stamina", "+1 Health", "+1 Damage",
    "+1 Protection", "+1 Dice Face", "+1 Inventory Slot", "ArmorReinforcementPaste", "ForestLuckCharm", "AntlerHood",
    "StonyHideLegwraps", "Small Meat", "Medium Meat", "Large Meat", "Basic Healing Poultice", "Wound Salve",
    "Poison Cleanser", "Spiked Collar", "Defense Wrap", "Fur Hood", "Fur Vest", "Fur Legwraps",
    "Hide Hood", "Hide Vest", "Hide Legwraps", "Stamina Tonic", "Strong Healing Mixture",
    "Bone Hood", "Bone Vest", "Bone Legwraps",
}


class BountySystem:
    def __init__(self, item_values, creature_templates):
        self.item_values = item_values
        self.creature_templates = creature_templates
        self.predators = [c.name for c in creature_templates if c.is_predator]

        # ✅ Define self.items BEFORE using it in reward_weights
        self.items = [
        k for k in item_values
        if k not in self.predators and k not in NONSENSE_TASK_ITEMS
        ]

        self.reward_weights = {
        item: max(1, int(100 / (1 + self.item_values[item])))  # Inverse weighting
        for item in self.items
        }

        self.creature_values = {
        c.name: (c.damage + c.health // 4) for c in creature_templates if c.is_predator
        }

    def generate_bounty(self):
        bounty_type = random.choice(["combat", "delivery", "gathering", "mixed"])
        if bounty_type == "combat":
            return self._generate_combat_bounty()
        elif bounty_type == "delivery":
            return self._generate_delivery_bounty()
        elif bounty_type == "gathering":
            return self._generate_gathering_bounty()
        else:
            return self._generate_mixed_bounty()

    def _generate_combat_bounty(self):
        target = random.choice(self.predators)
        num = random.randint(2, 5)
        target_value = self.creature_values.get(target, 10)
        total_value = target_value * num
        reward = self._choose_reward(total_value)
        return {
            "type": "combat",
            "task": f"Defeat {num} {target}(s)",
            "value": total_value,
            "reward": reward
        }

    def _generate_delivery_bounty(self):
        item = random.choice(self.items)
        num = random.randint(3, 8)
        total_value = self.item_values[item] * num * 0.9
        reward = self._choose_reward(total_value)
        return {"type": "delivery", "task": f"Deliver {num} {item}", "value": total_value, "reward": reward}

    def _generate_gathering_bounty(self):
        plant = random.choice(self.items)
        num = random.randint(3, 8)
        total_value = self.item_values[plant] * num * 0.9
        reward = self._choose_reward(total_value)
        return {"type": "gathering", "task": f"Gather {num} {plant}", "value": total_value, "reward": reward}

    def _generate_mixed_bounty(self):
        creature = random.choice(self.predators)
        item = random.choice(self.items)
        num_c = random.randint(1, 3)
        num_i = random.randint(2, 5)

        creature_value = self.creature_values.get(creature, 10)
        item_value = self.item_values[item]
        total_value = (creature_value * num_c + item_value * num_i) * 0.9

        reward = self._choose_reward(total_value)
        return {
            "type": "mixed",
            "task": f"Defeat {num_c} {creature}(s) and collect {num_i} {item}",
            "value": total_value,
            "reward": reward
        }

    def _choose_reward(self, total_value):
        candidates = [
            i for i in self.items
            if abs(self.item_values[i] - total_value) <= 10  # more forgiving range
        ]
        if not candidates:
            fallback = min(self.items, key=lambda x: abs(self.item_values[x] - total_value))
            return fallback

        # Use weighted random choice
        weights = [self.reward_weights[i] for i in candidates]
        return random.choices(candidates, weights=weights, k=1)[0]


    def get_available_bounties(self):
        return [self.generate_bounty() for _ in range(3)]


# Define the creature class
class Creature:
    def __init__(self, name, abbreviation, biome, damage, health, drops, exp_range, is_predator, status_effects=[], special_ability=None, luck=3, is_raid_boss=False):
        self.name = name
        self.abbreviation = abbreviation
        self.biome = biome
        self.damage = damage
        self.health = health
        self.max_health = health
        self.luck = luck
        self.drops = drops  # A dictionary of item drops and their chances
        self.exp_range = exp_range  # Tuple for EXP range (min, max) for random EXP drop
        self.is_predator = is_predator
        self.status_effects = status_effects  # Define possible status effects for this creature
        self.special_ability = special_ability
        self.escaped = False
        self.rage_triggered = False
        self.rage_type = None
        self.rage_turns_remaining = 0
        self.original_damage = self.damage
        self.is_raid_boss = is_raid_boss


    def __repr__(self):
        return f"{self.name}: - Damage: {self.damage}, Health: {self.health}"
    def display_header(title):
        print("\n╔═════⧗               ⧗═════╗")
        print(title.center(50))
        print("╚═════════════════════════════╝")

    def health_bar(current, max_health, width=20):
        filled = int(width * current / max_health)
        return "[" + "#" * filled + "-" * (width - filled) + "]"

    def display_health(entity):
        print(f"{entity.name}: {health_bar(entity.health, entity.max_health)} {entity.health}/{entity.max_health} HP")

    def log_action(action_text):
        print(f">> {action_text}")

    def reset_health(self):
        """Reset the creature's health to its maximum value."""
        self.health = self.max_health

    globals().update({
        "display_header": display_header,
        "health_bar": health_bar,
        "display_health": display_health,
        "log_action": log_action
    })

    def add_status_effect(self, effect):
        # Remove "none" if present
        if "none" in self.status_effects:
            self.status_effects.remove("none")

        # Add only if not already there
        if effect not in self.status_effects:
            self.status_effects.append(effect)


    def attack(self, target, attacker_name=None):
        #display_header((attacker_name or self.name) + "'s Turn")
        base_miss_chance = 0.05
        if self.luck < target.luck:
            luck_diff = min(target.luck - self.luck, 5)
            miss_chance = min(base_miss_chance + (luck_diff * 0.03), 0.65)
        else:
            miss_chance = base_miss_chance

        if random.random() < miss_chance:
            log_action(f"{self.name}'s attack misses {target.name}!")
            return

        if self.special_ability and random.random() <= 0.20:
            self.use_special_ability(target)
            return

        damage_dealt = max(self.damage - target.protection, 0)
        target.health -= damage_dealt
        log_action(f"{self.name} attacks {target.name} for {damage_dealt} damage after protection!")

        if hasattr(target, 'status_effects'):
            for effect in self.status_effects:
                if effect == 'poison' and 'poison' not in target.status_effects and random.random() < POISON_CHANCE:
                    target.add_status_effect('poison')
                    log_action(f"{self.name}'s venomous attack poisons {target.name}!")
                elif effect == 'bleeding' and 'bleeding' not in target.status_effects and random.random() < BLEED_CHANCE:
                    target.add_status_effect('bleeding')
                    log_action(f"{self.name}'s savage attack causes {target.name} to bleed!")
                elif effect == 'burn' and 'burn' not in target.status_effects and random.random() < BURN_CHANCE:
                    target.add_status_effect('burn')
                    log_action(f"{self.name}'s fiery scratch causes {target.name} to burn!")
                elif effect == 'RED_BLIGHT' and 'RED_BLIGHT' not in target.status_effects and random.random() < RED_CHANCE:
                    target.add_status_effect('RED_BLIGHT')
                    log_action(f"{self.name}'s corrupted attack infects {target.name} with RED_BLIGHT!")

        if target.health <= 0:
            log_action(f"{target.name} has been defeated!")

    def use_special_ability(self, target):
        log_action(f"{self.name} activates special ability: {self.special_ability.replace('_', ' ').upper()}")

        def deal_and_log(dmg, message):
            effective_damage = max(dmg - target.total_protection, 0)
            target.health -= effective_damage
            log_action(f"{message} ({effective_damage} after protection!)")
            display_health(target)

        if self.special_ability == "frenzied_bite":
            damage = self.damage * 2
            deal_and_log(damage, f"{self.name} lunges in a frenzy, biting {target.name} for {damage} damage!")

        elif self.special_ability == "crushing_pounce":
            damage = int(self.damage * 1.5)
            deal_and_log(damage, f"{self.name} leaps with a crash, crushing {target.name} for {damage} damage!")

        elif self.special_ability == "run_away":
            flee_chance = 0.4  # 40% chance to flee
            if random.random() < flee_chance:
                log_action(f"{self.name} panics and flees into the underbrush! It escapes the battle.")
                self.health = 0  # Use 0 HP to "remove" them from battle
            else:
                log_action(f"{self.name} tries to run, but {target.name} blocks the path!")


        elif self.special_ability == "savage_maul":
            damage = self.damage * 3
            deal_and_log(damage, f"{self.name} savagely mauls {target.name}, dealing {damage} damage!")

        elif self.special_ability == "rapid_lunge":
            damage = self.damage * 2
            deal_and_log(damage, f"{self.name} darts forward, striking {target.name} twice for {damage} total damage!")

        elif self.special_ability == "reckless_charge":
            damage = int(self.damage * 1.8)
            self.health -= 5
            deal_and_log(damage, f"{self.name} recklessly charges into {target.name} for {damage} damage but takes 5 recoil!")

        elif self.special_ability == "ripping_frenzy":
            damage = int(self.damage * 1.5)
            heal = int(damage * 0.5)
            deal_and_log(damage, f"{self.name} rips into {target.name} for {damage} damage, healing for {heal}!")
            self.health = min(self.max_health, self.health + heal)

        elif self.special_ability == "skull_slam":
            damage = int(self.damage * 0.75)
            deal_and_log(damage, f"{self.name} slams into {target.name} for {damage} damage!")
            if random.random() <= 0.5:
                target.add_status_effect('dazed')
                log_action(f"{target.name} is left dazed and staggering!")

        elif self.special_ability == "vein_piercer":
            damage = int(self.damage * 1.5)
            deal_and_log(damage, f"{self.name} strikes deep—{target.name} takes {damage} damage!")
            target.add_status_effect('bleeding')
            log_action(f"Blood sprays—{target.name} is now bleeding!")

        elif self.special_ability == "brutal_slam":
            damage = int(self.damage * 1.8)
            deal_and_log(damage, f"{self.name} delivers a brutal slam to {target.name}, dealing {damage} damage!")
            if random.random() <= 0.5:
                target.add_status_effect('dazed')
                log_action(f"{target.name} collapses back—dazed and vulnerable!")

        elif self.special_ability == "venom_lash":
            damage = int(self.damage * 1.2)
            deal_and_log(damage, f"{self.name} lashes out with venom, dealing {damage} to {target.name}!")
            target.add_status_effect('poison')
            log_action(f"{target.name} begins to twitch—poison floods their veins!")
        elif self.special_ability == "corrupt_fang":
            damage = int(self.damage * 1.4)
            deal_and_log(damage, f"{self.name}'s fangs pulse with rot, biting {target.name} for {damage} damage!")
            target.add_status_effect('RED_BLIGHT')
            log_action(f"Dark veins spread from the wound—{target.name} is infected with RED_BLIGHT!")
        elif self.special_ability == "howl_of_decay":
            damage = int(self.damage * 1.2)
            deal_and_log(damage, f"{self.name} howls with twisted fury, clawing {target.name} for {damage} damage!")
            target.add_status_effect('RED_BLIGHT')
            log_action(f"{target.name} reels—their blood carries the red corruption now!")
        elif self.special_ability == "blight_crush":
            damage = int(self.damage * 1.6)
            deal_and_log(damage, f"{self.name} slams its grotesque body into {target.name}, dealing {damage} damage!")
            if random.random() < 0.75:
                target.add_status_effect('RED_BLIGHT')
                log_action(f"The impact drives the corruption deep—{target.name} is infected with RED_BLIGHT!")




    def is_prey(self):
        return self.name in PREY_NAMES

    def attempt_escape_creature(self, battle):
        ESCAPE_CHANCE = 0.25 + (self.luck / 100)  # 25% base + luck bonus
        if self.is_prey() and self.health < self.max_health * 0.6:
            if random.random() < ESCAPE_CHANCE:
                log_action(f"{self.name} panics and flees the battle!")
                battle.creatures.remove(self)
                return True
        return False


    def apply_status_effects(self, target):
        """Apply ongoing effects if applicable."""
        for effect in self.status_effects:
            if effect == 'poison' and 'poison' not in target.status_effects:
                if random.random() < POISON_CHANCE:
                    print(f"{self.name}'s venomous attack poisons {target.name}!")
                    target.add_status_effect('poison')

            elif effect == 'bleeding' and 'bleeding' not in target.status_effects:
                if random.random() < BLEED_CHANCE:
                    print(f"{self.name}'s savage attack causes {target.name} to bleed!")
                    target.add_status_effect('bleeding')

            elif effect == 'shadow_shroud' and 'shadow shroud' not in target.status_effects:
                if random.random() < SHADOW_CHANCE:
                    print(f"{self.name}'s dark presence envelops {target.name} in shadows!")
                    target.add_status_effect('shadow shroud')

    def generate_drops(self):
        """Generate drops based on drop percentages and return the total EXP earned."""
        drops_gained = {}
        for item, chance in self.drops.items():
            if random.random() < chance:
                quantity = random.randint(1, 3)  # Randomly determine a quantity (1 to 3) of the item to drop
                drops_gained[item] = drops_gained.get(item, 0) + quantity  # Increment the drop count

        # Generate EXP from the defined range
        exp_earned = random.randint(*self.exp_range)
        return drops_gained, exp_earned

class Plant:
    def __init__(self, name, biome, gather_chance, effects=None):
        self.name = name
        self.biome = biome
        self.gather_chance = gather_chance  # Chance to successfully gather (0.0 to 1.0)
        self.effects = effects or {}  # Dictionary of effects this plant can have


# Define the item class
class Item:
    def __init__(self, name, effects: dict):
        self.name = name
        self.effects = effects
        self.item_type = self.determine_item_type()  # ← THIS LINE IS MANDATORY
        self.abbreviation = self.generate_abbreviation()

    def determine_item_type(self):
        # Automatically figure out the type from the effects
        if "heal" in self.effects:
            return "heal"
        elif "stamina" in self.effects:
            return "stamina"
        elif "boost_protection" in self.effects:
            return "boost"
        elif "remove_status" in self.effects:
            return "remove_status"
        else:
            return "misc"

    def generate_abbreviation(self):
        words = self.name.split()
        if len(words) == 1:
            return words[0][:2].upper()
        return ''.join(word[0] for word in words).upper()

    def use(self, target):
        effect_removers = {
            "Wound Salve": "bleeding",
            "Poison Cleanser": "poison",
            "Catmint": "illness",
            "Burdock Root": "poison",
            "Corrupted Cleanse": "RED_BLIGHT",
            "Moonstone Tonic": "RED_BLIGHT",
        }

        if self.name in ("Corrupted Cleanse", "Moonstone Tonic"):
            if "RED_BLIGHT" not in target.status_effects:
                print("But there was no RED_BLIGHT to cure.")
                return

            if self.name == "Corrupted Cleanse":
                print("The mixture burns going down. You feel feverish, your limbs shake—then silence. You wait to see if it worked…")
                target.status_effects.remove("RED_BLIGHT")
                print(f"{target.name}'s RED_BLIGHT has been purged!")
                return

            if self.name == "Moonstone Tonic":
                print("Your body seizes as if remembering the corruption all at once. But then… it lifts. The red haze fades.")
                if random.random() <= 0.55:
                    target.status_effects.remove("RED_BLIGHT")
                    print(f"{target.name}'s RED_BLIGHT has been cured!")
                else:
                    print("But the corruption holds fast. No effect.")
                return

        for effect, value in self.effects.items():
            if effect == "heal":
                target.health = min(target.max_health, target.health + value)
                print(f"{target.name} heals {value} HP!")

            elif effect == "stamina":
                target.stamina = min(target.stamina + value, target.max_stamina)
                print(f"{target.name} regains {value} stamina!")

            elif effect == "boost_protection":
                target.temp_protection += value
                print(f"{target.name} gains {value} protection!")

            elif effect == "remove_status":
                effect_to_remove = effect_removers.get(self.name)

                if isinstance(target.status_effects, list):
                    matching_effect = next((s for s in target.status_effects if s.lower().strip() == effect_to_remove.lower()), None)
                    if matching_effect:
                        target.status_effects.remove(matching_effect)
                        print(f"✅ {target.name} uses {self.name} and no longer feels the '{effect_to_remove}' status effect!")
                    else:
                        print(f"❌ {target.name} does not have '{effect_to_remove}' status effect!")
                else:
                    print("❌ status_effects is not a list, cannot remove anything.")

        status_effects = ','.join(target.status_effects) if target.status_effects else "None"
        print(target.to_line())

# Shortcut constructor
cls = lambda name, effects: Item(name, effects)

# 🌿 Real in-game items with multi-effects
game_items = {
    item.name: item for item in [
        cls("Small Meat", {"heal": 5, "stamina": 3}),
        cls("Medium Meat", {"heal": 15, "stamina": 5}),
        cls("Large Meat", {"heal": 25, "stamina": 10}),
        cls("Dock Leaves", {"heal": 10}),
        cls("Goldenrod", {"heal": 15}),
        cls("Comfrey Root", {"heal": 20}),
        cls("Basic Healing Poultice", {"heal": 45}),
        cls("Strong Healing Mixture", {"heal": 80}),
        cls("Marigold", {"heal": 12}),
        
        cls("Stamina Tonic", {"stamina": 20}),
        cls("Juniper Berries", {"stamina": 10}),
        cls("Poppy Seeds", {"stamina": 10}),
        
        cls("Blackberry Leaves", {"boost_protection": 4}),
        cls("Defense Wrap", {"boost_protection": 8}),
        
        cls("Wound Salve", {"remove_status": 0}),
        cls("Poison Cleanser", {"remove_status": 0}),
        cls("Catmint", {"remove_status": 0}),
        cls("Burdock Root", {"remove_status": 0}),
        
        cls("Corrupted Cleanse", {"remove_status": 0}),
        cls("Moonstone Tonic", {"remove_status": 0}),
    ]
}

class ShadowLottery:
    def __init__(self):
        self.prizes = {
            'Armor': [
                'Woven Hood', 'Woven Vest', 'Woven Legwraps',
                'Fur Hood', 'Fur Vest', 'Fur Legwraps',
                'Hide Hood', 'Hide Vest', 'Hide Legwraps',
                'Bone Hood', 'Bone Vest', 'Bone Legwraps'
            ],
            'Accessories': [
                'Spiked Collar'
            ],
            'Materials': [
                'Grass', 'Fur', 'Hide', 'Bone', 'Claw', 'Tooth', 'Feather', 'Scale', 'Shell', 'Venom Gland', 'Rotten Meat'
            ],
            'Consumables': [
                'Dock Leaves', 'Goldenrod', 'Blackberry Leaves', 'Comfrey Root',
                'Basic Healing Poultice', 'Wound Salve', 'Poison Cleanser', 
                'Stamina Tonic', 'Strong Healing Mixture', 'Defense Wrap'
            ],
            'Stats': [
                '+1 Luck', '+1 Damage', '+1 Health', '+1 Protection',
                '+1 Stamina', '+1 Inventory Slot', '+1 Dice Face',
                'Frantic Licks Ability', 'Bristle Ability', 'Noxious Snarl Ability', 'TAUNT', '5 Pawmarks', '1 Pawmarks'
            ],
            'Food': [
                'Small Meat', 'Medium Meat', 'Large Meat'
            ]
        }

        # Rarity weighting per category (lower weight = rarer)
        self.category_weights = {
            'Armor': 5,
            'Accessories': 3,
            'Stats': 1,
            'Materials': 10,
            'Consumables': 8,
            'Food': 12
        }

    def draw_lottery(self, num_draws=1):
        results = []

        categories = list(self.prizes.keys())
        weights = [self.category_weights[cat] for cat in categories]

        for _ in range(num_draws):
            # Draw category with weights
            category = random.choices(categories, weights=weights, k=1)[0]
            item = random.choice(self.prizes[category])

            results.append({
                'category': category,
                'item': item
            })
        return results

class KymeraDynamicShop:
    def __init__(self, item_values):
        self.item_values = item_values

    def generate_trade(self):
        offered_item = random.choice(list(self.item_values))
        target_value = self.item_values[offered_item]
        options = [i for i in self.item_values if i != offered_item and abs(self.item_values[i] - target_value) <= 5]
        if not options:
            return None
        requested_items = random.choices(options, k=random.randint(1, 2))
        return {
            "Kymera Offers": offered_item,
            "She Wants": requested_items
        }

    def generate_shop(self, trades=10):
        result = []
        for _ in range(trades):
            trade = self.generate_trade()
            if trade:
                offer_line = f"⭐ Kymera Offers: {trade['Kymera Offers']}\n🔻 She Wants: {', '.join(trade['She Wants'])}"
                result.append(offer_line)
        return "\n\n".join(result)

class CraftingSystem:
    def __init__(self):
        # Define potion abbreviations in the CraftingSystem class
        self.recipes = {
             # Healing / Consumables
            "BasicHealingPoultice": {
                "ingredients": {
                    "Dock Leaves": 2,
                    "Marigold": 2
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },
            "WoundSalve": {
                "ingredients": {
                    "Marigold": 3,
                    "Horsetail": 2
                },
                "success_rate": 0.6,
                "result_quantity": 1
            },
            "PoisonCleanser": {
                "ingredients": {
                    "Burdock Root": 3,
                    "Water Source": 1
                },
                "success_rate": 0.6,
                "result_quantity": 1
            },
            "StaminaTonic": {
                "ingredients": {
                    "Juniper Berries": 3
                },
                "success_rate": 0.5,
                "result_quantity": 1
            },
            "StrongHealingMixture": {
                "ingredients": {
                    "Goldenrod": 3,
                    "Comfrey Root": 2
                },
                "success_rate": 0.5,
                "result_quantity": 1
            },
            "DefenseWrap": {
                "ingredients": {
                    "Blackberry Leaves": 2,
                    "Dock Leaves": 2
                },
                "success_rate": 0.5,
                "result_quantity": 1
            },

            # Armor Reinforcement & Utility Items
            "ArmorReinforcementPaste": {
                "ingredients": {
                    "Sap": 3,
                    "Root": 2,
                    "Pinecone": 2
                },
                "success_rate": 0.95,
                "result_quantity": 1
            },
            "ForestLuckCharm": {
                "ingredients": {
                    "Pinecone": 1,
                    "Stick": 2,
                    "Moss": 2
                },
                "success_rate": 0.85,
                "result_quantity": 1
            },

            # New Armor Pieces
            "AntlerHood": {
                "ingredients": {
                    "Antler": 2,
                    "Fur": 2,
                    "Bone": 1
                },
                "success_rate": 0.85,
                "result_quantity": 1
            },

            "StonyHideLegwraps": {
                "ingredients": {
                    "Stone": 3,
                    "Hide": 2,
                    "Sap": 2
                },
                "success_rate": 0.85,
                "result_quantity": 1
            },

            # Woven Armor Set
            "WovenHood": {
                "ingredients": {
                    "Grass": 6,
                    "Dock Leaves": 2
                },
                "success_rate": 0.9,
                "result_quantity": 1
            },
            "WovenVest": {
                "ingredients": {
                    "Grass": 10,
                    "Dock Leaves": 3
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },
            "WovenLegwraps": {
                "ingredients": {
                    "Grass": 8,
                    "Dock Leaves": 2
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },

            # Fur Armor Set
            "FurHood": {
                "ingredients": {
                    "Fur": 6,
                    "Grass": 2,
                    "Dock Leaves": 2
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },
            "FurVest": {
                "ingredients": {
                    "Fur": 10,
                    "Grass": 3,
                    "Dock Leaves": 3
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },
            "FurLegwraps": {
                "ingredients": {
                    "Fur": 8,
                    "Grass": 2,
                    "Dock Leaves": 2
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },

            # Hide Armor Set
            "HideHood": {
                "ingredients": {
                    "Hide": 6,
                    "Fur": 3,
                    "Bone": 2
                },
                "success_rate": 0.85,
                "result_quantity": 1
            },
            "HideVest": {
                "ingredients": {
                    "Hide": 10,
                    "Fur": 4,
                    "Bone": 3
                },
                "success_rate": 0.85,
                "result_quantity": 1
            },
            "HideLegwraps": {
                "ingredients": {
                    "Hide": 8,
                    "Fur": 3,
                    "Bone": 2
                },
                "success_rate": 0.85,
                "result_quantity": 1
            },

            # Bone Armor Set
            "BoneHood": {
                "ingredients": {
                    "Hide": 5,
                    "Bone": 5,
                    "Fur": 2
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },
            "BoneVest": {
                "ingredients": {
                    "Hide": 8,
                    "Bone": 8,
                    "Fur": 3
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },
            "BoneLegwraps": {
                "ingredients": {
                    "Hide": 6,
                    "Bone": 6,
                    "Fur": 2
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },

            "ShellPendant": {
                "ingredients": {
                    "Shell": 3,
                    "Seaweed": 2
                },
                "success_rate": 0.8,
                "result_quantity": 1
            },

            # Accessory
            "SpikedCollar": {
                "ingredients": {
                    "Hide": 4,
                    "Claw": 2,  # or Tooth x2, you can check inside your code logic later
                    "Bone": 2
                },
                "success_rate": 0.85,
                "result_quantity": 1
            }
        }

    def craft_item(self, player, recipe_name, inventory):
        if recipe_name not in self.recipes:
            print(f"Recipe for {recipe_name} not found!")
            return False

        recipe = self.recipes[recipe_name]

        # Display recipe ingredients regardless of crafting outcome
        print("\nIngredients used for this recipe:")
        for ingredient, amount in recipe["ingredients"].items():
            print(f"- {amount}x {ingredient}")
            print("")

        # Determine and display crafting outcome
        if random.random() <= recipe["success_rate"]:
            print("")
            print("")
            print(f"Successfully crafted {recipe['result_quantity']} {recipe_name}!")
            return True
        print("")
        print("")
        print(f"Failed to craft {recipe_name}!")
        return False


# Define player character class
class PlayerCharacter:
    def __init__(self, name, max_health, health, stamina, max_stamina, luck,
                 protection, light, damage, status_effects,
                 temp_damage=0, temp_protection=0, rest_counter=0, current_nest="Broken Nest"):
        self.name = name
        self.max_health = max_health
        self.health = health
        self.stamina = stamina
        self.max_stamina = max_stamina  # New attribute for max stamina
        self.luck = luck
        self.protection = protection
        self.light = light
        self.damage = damage
        self.temp_damage = temp_damage
        self.temp_protection = temp_protection
        try:
            # If it's a proper list already, use it
            self.status_effects = status_effects if isinstance(status_effects, list) else ast.literal_eval(status_effects)
        except:
            self.status_effects = [] # List to track status effects
        self.inventory = []  # Initialize inventory for items
        self.temp_damage = 0
        self.temp_protection = 0
        self.rest_counter = rest_counter
        self.current_nest = current_nest

    @property
    def total_damage(self):
        return self.damage + self.temp_damage

    @property
    def total_protection(self):
        return self.protection + self.temp_protection

    def __repr__(self):
        return f"{self.name}: HP={self.health}/{self.max_health}, Stamina={self.stamina}/{self.max_stamina}, Luck={self.luck}, Protection={self.protection}, Light={self.light}, Damage={self.damage}, Status Effects={self.status_effects}"

    def display_header(title):
        print("\n╔═════⧗               ⧗═════╗")
        print(title.center(50))
        print("╚═════════════════════════════╝")

    def health_bar(current, max_health, width=20):
        filled = int(width * current / max_health)
        return "[" + "#" * filled + "-" * (width - filled) + "]"

    def display_health(entity):
        print(f"{entity.name}: {health_bar(entity.health, entity.max_health)} {entity.health}/{entity.max_health} HP")

    def log_action(action_text):
        print(f">> {action_text}")

    globals().update({
        "display_header": display_header,
        "health_bar": health_bar,
        "display_health": display_health,
        "log_action": log_action
    })
    @staticmethod
    def from_input():
        print("\n" * 21)
        while True:
            try:
                data_line = input("Please PASTE Character Line!: ").strip()
                parts = data_line.split(",")
                if len(parts) < 9:
                    print("[!] Not enough values. Please enter the full stat line.")
                    continue

                name = parts[0]
                max_health = int(parts[1])
                health = int(parts[2])
                stamina = int(parts[3])
                max_stamina = int(parts[4])
                luck = int(parts[5])
                protection = int(parts[6])
                light = int(parts[7])
                damage = int(parts[8])
                temp_damage = int(parts[9]) if len(parts) > 9 else 0
                temp_protection = int(parts[10]) if len(parts) > 10 else 0
                rest_counter = int(parts[11]) if len(parts) > 11 else 0
                current_nest = parts[12] if len(parts) > 12 else "Broken Nest"

                # Grab everything after index 12 as status effects
                status_effects = parts[13:] if len(parts) > 13 else []
                cleaned_effects = [s.strip() for s in status_effects if s.strip().lower() != "none" and s.strip() != ""]

                return PlayerCharacter(
                    name, max_health, health, stamina, max_stamina, luck,
                    protection, light, damage, cleaned_effects,
                    temp_damage=temp_damage, temp_protection=temp_protection,
                    rest_counter=rest_counter, current_nest=current_nest
                )

            except ValueError:
                print("[!] Invalid input format. Please try again.")
            except (EOFError, KeyboardInterrupt):
                print("\n[!] Input failed or was interrupted. Please try again.")

    def clamp_stats(self):
        if self.stamina < 0:
            self.stamina = 0
        if self.health < 0:
            self.health = 0
    def to_line(self):
        status_part = ','.join(self.status_effects) if self.status_effects else 'None'
        return f"{self.name},{self.max_health},{self.health},{self.stamina},{self.max_stamina},{self.luck},{self.protection},{self.light},{self.damage},{self.temp_damage},{self.temp_protection},{self.rest_counter},{self.current_nest},{status_part}"

    def add_status_effect(self, effect):
        # Remove "none" if present
        if "none" in self.status_effects:
            self.status_effects.remove("none")

        # Add only if not already there
        if effect not in self.status_effects:
            self.status_effects.append(effect)

    def groom_wounds(self, target):
        heal_amount = 5
        target.health = min(target.health + heal_amount, target.max_health)
        display_header(self.name + "'s Turn")
        log_action(f"{self.name} grooms {target.name}'s wounds, restoring {heal_amount} HP!")
        display_health(target)

    def taunt(self, battle):
        display_header(self.name + "'s Turn")
        if self.stamina >= 5:
            self.stamina -= 5
            battle.taunted_by = self
            battle.taunt_turns_remaining = 5  # Lasts 5 turns
            log_action(f"{self.name} lets out a loud taunt, drawing all enemy attention for 5 turns!")
        else:
            log_action(f"{self.name} doesn't have the strength to taunt!")

    def field_tend(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 3:
            heal_amount = 25
            self.stamina -= 5
            self.clamp_stats()
            target.health = min(target.max_health, target.health + heal_amount)
            log_action(f"{self.name} tends to {target.name}'s injuries, restoring {heal_amount} HP!")
            display_health(target)
        else:
            log_action(f"{self.name} is too exhausted to tend wounds!")

    def frantic_licks(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 30:
            heal_amount = 50
            self.stamina -= 30
            self.clamp_stats()
            target.health = min(target.max_health, target.health + heal_amount)
            log_action(f"{self.name} frantically licks {target.name}'s wounds, restoring {heal_amount} HP!")
            display_health(target)
        else:
            log_action(f"{self.name} is too drained to help!")

    def quick_nudge(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 7:
            heal_amount = 15
            self.stamina -= 7
            self.clamp_stats()
            target.health = min(target.max_health, target.health + heal_amount)
            log_action(f"{self.name} urgently nudges {target.name} back on their paws, healing {heal_amount} HP!")
            display_health(target)
        else:
            log_action(f"{self.name} is too tired to help!")

    def bristle(self):
        display_header(self.name + "'s Turn")
        if self.stamina >= 3:
            self.stamina -= 3
            self.clamp_stats()
            additional_protection = 5
            self.temp_protection += additional_protection
            log_action(f"{self.name} bristles defensively, gaining {additional_protection} protection!")
        else:
            log_action(f"{self.name} is too weary to brace themselves!")

    def defensive_crouch(self):
        display_header(self.name + "'s Turn")
        if self.stamina >= 10:
            self.stamina -= 10
            self.clamp_stats()
            additional_protection = 10
            self.temp_protection += additional_protection
            log_action(f"{self.name} drops into a defensive crouch, gaining {additional_protection} protection!")
        else:
            log_action(f"{self.name} cannot muster the strength to crouch!")

    def heavy_pounce(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 10:
            self.stamina -= 10
            extra_damage = 10
            total_damage = self.damage + extra_damage
            target.health -= total_damage
            log_action(f"{self.name} delivers a heavy pounce onto {target.name}, causing {total_damage} damage!")
            display_health(target)
        else:
            log_action(f"{self.name} is too tired to pounce!")

    def precise_lunge(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 13:
            self.stamina -= 13
            self.clamp_stats()
            extra_damage = 15
            total_damage = self.damage + extra_damage
            target.health -= total_damage
            log_action(f"{self.name} lunges precisely at {target.name}, causing {total_damage} damage!")
            display_health(target)
        else:
            log_action(f"{self.name} lacks the strength to lunge!")

    def noxious_snarl(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 7:
            self.stamina -= 7
            extra_damage = 10
            total_damage = self.damage + extra_damage
            target.health -= total_damage
            log_action(f"{self.name} releases a noxious snarl, stunning {target.name} for {total_damage} damage!")
            display_health(target)
        else:
            log_action(f"{self.name} is too drained to snarl!")

    def maul(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 30:
            self.stamina -= 30
            self.clamp_stats()
            damage_per_hit = self.damage
            total_damage = damage_per_hit * 3
            target.health -= total_damage
            log_action(f"{self.name} mauls {target.name} savagely, dealing {total_damage} damage!")
            display_health(target)
        else:
            log_action(f"{self.name} can't muster the energy to maul!")

    def double_claw(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 6:
            self.stamina -= 6
            damage_per_hit = self.damage
            total_damage = damage_per_hit * 2
            target.health -= total_damage
            log_action(f"{self.name} strikes {target.name} with a rapid double claw swipe for {total_damage} damage!")
            display_health(target)
        else:
            log_action(f"{self.name} can't claw fast enough!")

    def shoulder_slam(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 10:
            self.stamina -= 10
            damage_per_hit = self.damage
            total_damage = damage_per_hit * 3
            target.health -= total_damage
            log_action(f"{self.name} slams their shoulder into {target.name}, causing {total_damage} damage!")
            display_health(target)
        else:
            log_action(f"{self.name} stumbles and cannot slam!")

    def ram_charge(self, target):
        display_header(self.name + "'s Turn")
        if self.stamina >= 20:
            self.stamina -= 20
            additional_protection = 5
            self.temp_protection += additional_protection
            extra_damage = 5
            total_damage = self.damage + extra_damage
            target.health -= total_damage
            log_action(f"{self.name} rams into {target.name}, dealing {total_damage} damage and gaining {additional_protection} protection!")
            display_health(target)
        else:
            log_action(f"{self.name} fumbles and can't ram!")
    def war_howl(self):
        display_header(self.name + "'s Turn")
        if self.stamina >= 4:
            self.stamina -= 4
            damage_boost = 5

            print("Available allies to empower:")
            for i, player in enumerate(players, 1):
                if player != self:
                    print(f"{i}. {player.name} (Current damage: {player.damage})")

            while True:
                try:
                    choice = int(input("\nChoose an ally to empower (enter number): ")) - 1
                    if 0 <= choice < len(players) and players[choice] != self:
                        target = players[choice]
                        target.damage += damage_boost
                        log_action(f"{self.name} howls fiercely, empowering {target.name} with +{damage_boost} damage!")
                        log_action(f"{target.name}'s new damage: {target.damage}")
                        break
                    else:
                        print("Invalid choice. Passed.")
                        break
                except ValueError:
                    print("Please enter a valid number.")
        else:
            log_action(f"{self.name} doesn't have enough breath to howl!")





    # Use an item
    def use_item(self, item):
        item.use(self)

    def apply_status_effects(self):
        """Apply ongoing effects like RED_BLIGHT, bleeding, poison, or burn if active."""
        total_damage = 0

        if 'RED_BLIGHT' in self.status_effects:
            print(f"{self.name} is wracked by RED_BLIGHT and loses {RED_BLIGHT_DAMAGE} HP!")
            self.health -= RED_BLIGHT_DAMAGE
            total_damage += RED_BLIGHT_DAMAGE

        if 'bleeding' in self.status_effects:
            print(f"{self.name} is bleeding and loses {BLEED_DAMAGE} HP!")
            self.health -= BLEED_DAMAGE
            total_damage += BLEED_DAMAGE

        if 'burn' in self.status_effects:
            print(f"{self.name} is burning and loses {BURN_DAMAGE} HP!")
            self.health -= BURN_DAMAGE
            total_damage += BURN_DAMAGE

        if 'poison' in self.status_effects:
            print(f"{self.name} is poisoned and loses {POISON_DAMAGE} HP!")
            self.health -= POISON_DAMAGE
            total_damage += POISON_DAMAGE

        self.clamp_stats()

        if self.health <= 0:
            print(f"💀 {self.name} has succumbed to their status effects and collapses!")

        if 'dazed' in self.status_effects:
            print(f"{self.name} is dazed and cannot act this turn.")
            self.status_effects.remove('dazed')
            return True  # Can't act

        return False  # Can act


    def clear_temp_stats(self):
        self.temp_damage = 0
        self.temp_protection = 0

class FarmingSystem:
    def __init__(self):
        self.crops = {
            "Dock Leaves": {"base_yield": 3, "abbrev": "DL"},
            "Goldenrod": {"base_yield": 2, "abbrev": "GR"},
            "Blackberry Leaves": {"base_yield": 3, "abbrev": "BL"},
            "Comfrey Root": {"base_yield": 2, "abbrev": "CR"},
            "Marigold": {"base_yield": 2, "abbrev": "MR"},
            "Horsetail": {"base_yield": 2, "abbrev": "HT"},
            "Juniper Berries": {"base_yield": 3, "abbrev": "JB"},
            "Poppy Seeds": {"base_yield": 1, "abbrev": "PS"},
            "Burdock Root": {"base_yield": 2, "abbrev": "BR"},
            "Catmint": {"base_yield": 1, "abbrev": "CM"}  # rare, low yield
        }

        self.weather_effects = {
            "Drought": 0.5,   # Dry and harsh, low yield
            "Stormy": 0.75,   # Heavy rain, weak yield
            "Cloudy": 1.0,    # Normal
            "Rainy": 1.5      # Perfect growing weather
        }

    def plant_and_harvest(self):
        print("\n=== FARMING MENU ===")
        print("Available herbs to plant:")
        for crop, info in self.crops.items():
            print(f"{info['abbrev']} - {crop}")

        has_lifebloom = input("\nDo they have the Lifebloom Harvester title? (y/n): ").lower() == 'y'

        while True:
            print("\nCurrent weather conditions:")
            print("1. Drought")
            print("2. Stormy")
            print("3. Cloudy")
            print("4. Rainy")
            weather_choice = input("Enter current weather (1-4): ")

            weather_map = {"1": "Drought", "2": "Stormy", "3": "Cloudy", "4": "Rainy"}
            if weather_choice in weather_map:
                current_weather = weather_map[weather_choice]
                break
            print("Invalid weather choice. Please try again.")

        crop_input = input("\nWhich herb would you like to plant? (enter abbreviation): ").upper()
        selected_crop = None
        for crop, info in self.crops.items():
            if info['abbrev'] == crop_input:
                selected_crop = crop
                break

        if not selected_crop:
            print("Invalid crop selection!")
            return

        # Calculate harvest
        base_yield = self.crops[selected_crop]['base_yield']
        weather_multiplier = self.weather_effects[current_weather]
        final_yield = int(base_yield * weather_multiplier)

        if has_lifebloom:
            final_yield += 2  # Smaller bonus now for balance

        print("\n=== HARVEST RESULTS ===")
        print(f"Weather: {current_weather}")
        print(f"Harvested {final_yield}x {selected_crop}")


# Battle system
class Battle:
    def __init__(self, players, bounty_system):
        self.players = players
        self.bounty_system = bounty_system
        self.creatures = []
        self.escaped_players = []
        self.current_creature_index = 0  # Track which creature is currently active
        self.total_drops = {}  # To store total drops from this battle
        self.total_exp = 0  # To store total experience gained in this battle
        self.items_used = {}
        self.taunted_by = None  # Tracks which player has taunted
        self.taunt_turns_remaining = 0
        self.temp_boosts = {
            player.name: {
                'damage': 0,
                'protection': 0,
                'turns_remaining': 0
            } for player in players
        }

        # Create items
        self.items = list(game_items.values())


        # Define creatures with possible status effects and EXP ranges
        # Define creatures with updated stats, drops, locations
        self.creature_templates = [
            # 🛖 Cinderglen (Camp Area) Prey
            Creature("Sparrow", "sparrow", "Cinderglen", 1, 6, {"small meat": 0.8, "feather": 0.5}, (10, 20), False, [], special_ability="", luck=5),
            Creature("Rabbit", "rabbit", "Cinderglen", 4, 35, {"medium meat": 0.8, "fur": 0.5}, (10, 20), False, [], special_ability="", luck=8),
            Creature("Water Vole", "wvole", "Cinderglen", 1, 8, {"small meat": 0.8, "fur": 0.5}, (10, 20), False, [], special_ability="", luck=3),
            Creature("Small Fish", "sfish", "Cinderglen", 1, 5, {"small meat": 0.8, "scale": 0.5}, (10, 20), False, [], special_ability="", luck=9),
            Creature("Beetle", "beetle", "Cinderglen", 1, 3, {"scale": 0.8}, (10, 20), False, [], special_ability="", luck=4),
            Creature("Lizard", "lizard", "Cinderglen", 1, 5, {"small meat": 0.8, "scale": 0.5}, (10, 20), False, [], special_ability="", luck=5),

            # 🛖 Cinderglen Predators
            Creature("Weakened Fox", "wfox", "Cinderglen", 3, 25, {"fur": 0.5, "tooth": 0.2, "bone": 0.2}, (10, 20), True, [], special_ability="frenzied_bite", luck=12),
            #Creature("Blighted Fox", "bfox", "Cinderglen", 2, 35, {"fur": 0.5, "tooth": 0.2, "bone": 0.2}, (10, 20), True, [], special_ability="frenzied_bite", luck=12),
            Creature("Weakend Hawk", "whawk", "Cinderglen", 3, 28, {"feather": 0.5, "claw": 0.3, "bone": 0.2}, (10, 20), True, [], special_ability="rapid_lunge", luck=14),

            # 🌲 Whispering Pines (Forest) Prey
            Creature("Mouse", "mouse", "Whispering Pines", 2, 9, {"small meat": 0.8, "fur": 0.5}, (10, 20), False, [], special_ability="", luck=7),
            Creature("Squirrel", "squirrel", "Whispering Pines", 3, 28, {"small meat": 0.8, "fur": 0.5}, (10, 20), False, [], special_ability="", luck=23),
            Creature("Thrush", "thrush", "Whispering Pines", 2, 27, {"small meat": 0.8, "feather": 0.5}, (10, 20), False, [], special_ability="", luck=24),
            Creature("Blackbird", "blackbird", "Whispering Pines", 4, 29, {"small meat": 0.8, "feather": 0.5}, (10, 20), False, [], special_ability="", luck=23),
            Creature("Rabbit", "rabbit", "Whispering Pines", 4, 35, {"medium meat": 0.8, "fur": 0.5}, (10, 20), False, [], special_ability="", luck=8),

            # 🌲 Whispering Pines Predators
            Creature("Fox", "fox", "Whispering Pines", 10, 60, {"fur": 0.5, "tooth": 0.2, "bone": 0.2}, (10, 20), True, [], special_ability="frenzied_bite", luck=12),
            Creature("Hawk", "hawk", "Whispering Pines", 9, 50, {"feather": 0.5, "claw": 0.3, "bone": 0.2}, (10, 20), True, [], special_ability="rapid_lunge", luck=14),
            Creature("Owl", "owl", "Whispering Pines", 13, 48, {"feather": 0.5, "claw": 0.3, "bone": 0.2}, (10, 20), True, [], special_ability="crushing_pounce", luck=15),

            # 🏔️ Howler’s Rise (Mountains) Prey
            Creature("Mountain Hare", "mhare", "Howler's Rise", 4, 42, {"medium meat": 0.8, "fur": 0.5}, (10, 20), False, [], special_ability="", luck=18),
            Creature("Small Bird", "sbird", "Howler's Rise", 3, 30, {"small meat": 0.8, "feather": 0.5}, (10, 20), False, [], special_ability="", luck=27),
            Creature("Vole", "vole", "Howler's Rise", 3, 28, {"small meat": 0.8, "fur": 0.5}, (10, 20), False, [], special_ability="", luck=21),

            # 🏔️ Howler’s Rise Predators
            Creature("Eagle", "eagle", "Howler's Rise", 14, 77, {"feather": 0.5, "claw": 0.3, "bone": 0.2}, (10, 20), True, [], special_ability="skull_slam", luck=10),
            Creature("Badger", "badger", "Howler's Rise", 13, 75, {"fur": 0.5, "claw": 0.3, "bone": 0.2, "hide": 0.2}, (10, 20), True, [], special_ability="reckless_charge", luck=9),
            Creature("Wolverine", "wolverine", "Howler's Rise", 15, 100, {"fur": 0.5, "claw": 0.3, "bone": 0.2, "hide": 0.2}, (10, 20), True, [], special_ability="savage_maul", luck=8),

            # 🌑 Gathering Place (Deadlands) Predators
            Creature("Mutated Fox", "mfox", "Deadlands", 16, 300,
                 {"fur": 0.5, "tooth": 0.2, "bone": 0.2, "rotten meat": 0.1},
                 (10, 20), True, ["RED_BLIGHT"], special_ability="corrupt_fang", luck=10),

            Creature("Rabid Wolf", "rwolf", "Deadlands", 18, 400,
                 {"fur": 0.5, "tooth": 0.2, "bone": 0.2, "rotten meat": 0.1},
                 (10, 20), True, ["RED_BLIGHT"], special_ability="howl_of_decay", luck=8),

            Creature("Monstrous Rogue", "mrogue", "Deadlands", 20, 800,
                 {"fur": 0.5, "claw": 0.3, "bone": 0.2, "hide": 0.2, "rotten meat": 0.1},
                 (10, 20), True, ["RED_BLIGHT"], special_ability="blight_crush", luck=7),

            # 🌊 Blacktide Beach (Beach) Prey
            Creature("Trout", "trout", "Blacktide Beach", 4, 30, {"medium meat": 0.8, "scale": 0.5}, (10, 20), False, [], special_ability="", luck=21),
            Creature("Minnow", "minnow", "Blacktide Beach", 1, 18, {"small meat": 0.8, "scale": 0.5}, (10, 20), False, [], special_ability="", luck=28),
            Creature("Crab", "crab", "Blacktide Beach", 6, 45, {"small meat": 0.8, "shell": 0.5}, (10, 20), False, [], special_ability="", luck=18),

            # 🌊 Blacktide Beach Predators
            Creature("Gull", "gull", "Blacktide Beach", 6, 20, {"claw": 0.5, "feather": 0.5}, (10, 20), True, [], special_ability="rapid_lunge", luck=17),
            Creature("Crow", "crow", "Blacktide Beach", 5, 25, {"claw": 0.5, "feather": 0.5}, (10, 20), True, [], special_ability="frenzied_bite", luck=18),
            Creature("Sea Snake", "seasnake", "Blacktide Beach", 9, 45, {"scale": 0.5, "venom gland": 0.1}, (10, 20), True, [], special_ability="venom_lash", luck=14),
        ]


        self.plants = [
                # Howler's Rise
                Plant("Comfrey Root", "Howler's Rise", 0.7),
                Plant("Goldenrod", "Howler's Rise", 0.4),
                Plant("Horsetail", "Howler's Rise", 0.6),
                Plant("Rock", "Howler's Rise", 0.5),
                Plant("Antler", "Howler's Rise", 0.3),
                Plant("Root", "Howler's Rise", 0.4),

                # Whispering Pines
                Plant("Burdock Root", "Whispering Pines", 0.2),
                Plant("Dock Leaves", "Whispering Pines", 0.5),
                Plant("Juniper Berries", "Whispering Pines", 0.6),
                Plant("Marigold", "Whispering Pines", 0.5),
                Plant("Stick", "Whispering Pines", 0.6),
                Plant("Sap", "Whispering Pines", 0.5),
                Plant("Moss", "Whispering Pines", 0.4),
                Plant("Pinecone", "Whispering Pines", 0.5),

                # Cinderglen
                Plant("Blackberry Leaves", "Cinderglen", 0.4),
                Plant("Catmint", "Cinderglen", 0.8),
                Plant("Dock Leaves", "Cinderglen", 0.5),
                Plant("Grass", "Cinderglen ", 0.8),
                Plant("Thistle Patches", "Cinderglen", 0.5),
                Plant("Stone", "Cinderglen", 0.6),

                # Deadlands
                Plant("Shard", "Deadlands", 0.3),

                # Blacktide Beach
                Plant("Seaweed", "Blacktide Beach", 0.6)
            ]

        # Define creature encounter chances while gathering in each biome
        self.gathering_encounter_chances = {
            "Howler's Rise": 0.6,    # 30% chance to encounter creatures
            "Whispering Pines": 0.4, # 40% chance to encounter creatures
            "Cinderglen": 0.3, # 20% chance to encounter creatures
            "Deadlands": 0.7, # 20% chance to encounter creatures
            "Blacktide Beach": 0.4 # 20% chance to encounter creatures
        }

        self.biomes = {
            "Howler's Rise": self.creature_templates[:4],  # Howler's Rise creatures
            "Whispering Pines": self.creature_templates[4:8],  # Whispering Pines  creatures
            "Cinderglen": self.creature_templates[8:12],  # Cinderglen  creatures
            "Deadlands": self.creature_templates[12:16],  # Deadlands  creatures
            "Blacktide Beach": self.creature_templates[16:20]  # Blacktide Beach  creatures
        }

        # Define stamina costs for traveling between biomes
        self.travel_costs = {
            ("Howler's Rise", "Whispering Pines"): 10,
            ("Whispering Pines", "Howler's Rise"): 10,

            ("Whispering Pines", "Cinderglen"): 5,
            ("Cinderglen", "Whispering Pines"): 5,

            ("Cinderglen", "Deadlands"): 8,
            ("Deadlands", "Cinderglen"): 8,

            ("Cinderglen", "Blacktide Beach"): 8,
            ("Blacktide Beach", "Cinderglen"): 8,
        }

        self.RAID_BOSSES = [
            {
                "name": "Hollow Maw",
                "abbreviation": "HM",
                "damage": 4,
                "health": 850,
                "drops": {
                    "rotten meat": 0.9,
                    "fur": 0.6,
                    "+3DMG": 0.2,
                    "+5HP": 0.2,
                    "+2Protection": 0.01,
                    "+2Luck": 0.15,
                    "+2Inventory": 0.1,
                    "+1DMG": 0.2,
                    "+1HP": 0.2,
                    "+1Protection": 0.03,
                    "+1Luck": 0.15,
                    "+5 Pawmarks": 0.02,
                    "+1 Pawmarks": 0.10,
                    "+2Inventory": 0.01
                },
                "exp_range": (180, 250),
                "is_predator": True,
                "status_effects": ["bleeding"],
                "special_ability": "savage_maul",
                "luck": 9,
                "minions": ["Fox", "Weakened Fox"]
            },
            {
                "name": "Raivyr",
                "abbreviation": "R",
                "damage": 5,
                "health": 1250,
                "drops": {
                    "feather": 0.9,
                    "fur": 0.9,
                    "+3DMG": 0.06,
                    "+5HP": 0.2,
                    "+1Protection": 0.1,
                    "+4Luck": 0.15,
                    "+1DMG": 0.2,
                    "+1HP": 0.2,
                    "+1Protection": 0.18,
                    "+1Luck": 0.15,
                    "+5 Pawmarks": 0.02,
                    "+1 Pawmarks": 0.10,
                    "+2Inventory": 0.01
                },
                "exp_range": (180, 250),
                "is_predator": True,
                "status_effects": ["bleeding"],
                "special_ability": "savage_maul",
                "luck": 9,
                "minions": ["Crow", "Gull"]
            },
            {
                "name": "Carrion Crown",
                "abbreviation": "CC",
                "damage": 5,
                "health": 755,
                "drops": {
                    "feather": 0.9,
                    "bone": 0.6,
                    "+1DMG": 0.12,
                    "+2HP": 0.12,
                    "+1Protection": 0.1,
                    "+1Luck": 0.1,
                    "+1Inventory": 0.1,
                    "+1DMG": 0.2,
                    "+1HP": 0.2,
                    "+1Protection": 0.18,
                    "+1Luck": 0.15,
                    "+5 Pawmarks": 0.02,
                    "+1 Pawmarks": 0.10,
                    "+2Inventory": 0.01
                },
                "exp_range": (180, 250),
                "is_predator": True,
                "status_effects": ["poison"],
                "special_ability": "crushing_pounce",
                "luck": 8,
                "minions": ["Crow", "Gull"]
            },
            {
                "name": "Rot-Heart",
                "abbreviation": "RH",
                "damage": 3,
                "health": 950,
                "drops": {
                    "bone": 0.9,
                    "hide": 0.6,
                    "+4DMG": 0.25,
                    "+6HP": 0.25,
                    "+3Protection": 0.2,
                    "+2Luck": 0.15,
                    "+2Inventory": 0.12,
                    "+1DMG": 0.2,
                    "+1HP": 0.2,
                    "+5 Pawmarks": 0.02,
                    "+1 Pawmarks": 0.10,
                    "+1Protection": 0.18,
                    "+1Luck": 0.15,
                    "+2Inventory": 0.01
                },
                "exp_range": (180, 250),
                "is_predator": True,
                "status_effects": ["bleeding"],
                "special_ability": "vein_piercer",
                "luck": 7,
                "minions": ["Badger", "Wolverine"]
            },
            {
                "name": "Duskcoil",
                "abbreviation": "DS",
                "damage": 5,
                "health": 1200,
                "drops": {
                    "scale": 0.9,
                    "venom gland": 0.6,
                    "+2DMG": 0.15,
                    "+4HP": 0.15,
                    "+2Protection": 0.12,
                    "+1Luck": 0.12,
                    "+1Inventory": 0.1,
                    "+1DMG": 0.2,
                    "+1HP": 0.2,
                    "+5 Pawmarks": 0.02,
                    "+1 Pawmarks": 0.10,
                    "+1Protection": 0.18,
                    "+1Luck": 0.15,
                    "+2Inventory": 0.01
                },
                "exp_range": (180, 250),
                "is_predator": True,
                "status_effects": ["poison"],
                "special_ability": "venom_lash",
                "luck": 10,
                "minions": ["Sea Snake", "Crab"]
            }
        ]
        self.DROP_TIERS = {
            "low": {
                "common": [
                    'grass', 'fur', 'feather', 'shell', 'rotten meat',
                    'dock leaves', 'goldenrod', 'stick', 'moss', 'pinecone', 'rock'
                ],
                "uncommon": [
                    'blackberry leaves', 'comfrey root', 'horsetail',
                    'seaweed', 'small meat', 'root', 'sap', 'stone'
                ],
                "rare": [
                    'thistle patches', 'juniper berries', 'marigold',
                    'burdock root', 'antler'
                ]
            },
            "medium": {
                "common": [
                    'thistle patches', 'juniper berries', 'marigold',
                    'burdock root', 'root', 'sap', 'stone'
                ],
                "uncommon": [
                    'claw', 'tooth', 'scale', 'venom gland', 'medium meat',
                    'antler', 'armorreinforcementpaste', 'shardinfusion'
                ],
                "rare": [
                    'basic healing poultice', 'wound salve', 'poison cleanser',
                    'fur hood', 'fur vest', 'forestluckcharm'
                ]
            },
            "high": {
                "common": [
                    'large meat', 'stamina tonic', 'strong healing mixture',
                    'armorreinforcementpaste'
                ],
                "uncommon": [
                    'spiked collar', 'defense wrap', 'fur legwraps',
                    'hide hood', 'hide vest', 'hide legwraps',
                    'antlerhood', 'stonyhidelegwraps'
                ],
                "rare": [
                    '+1 damage', '+1 stamina', '+1 inventory slot',
                    'bone hood', 'bone vest', 'bone legwraps',
                    '+1 luck', '+1 health', '+1 protection',
                    '+1 dice face', 'shard'
                ]
            }
        }
    def get_item_rarity(self, drop_name):
        drop = drop_name.lower()
        for tier in self.DROP_TIERS.values():
            for rarity, drops in tier.items():
                if drop in drops:
                    return rarity
        return "unknown"
    def determine_rage_state(self, creature):
        # Only raid bosses can enter rage
        if not creature.is_raid_boss:
            return None

        if creature.rage_triggered:
            return None

        if creature.health <= creature.max_health * 0.5:
            creature.rage_triggered = True
            creature.rage_turns = 15

            rage_options = ["feral", "corrupted bloodlust", "feast"]
            creature.rage_type = random.choice(rage_options)
            return creature.rage_type

        return None

    def apply_rage_effects(creature, player_hit=None):
        """Ongoing rage effects."""
        if not creature.rage_mode:
            return

        if creature.rage_type == "bloodlust":
            effects = ["bleeding", "burn", "RED_BLIGHT"]
            effect = random.choice(effects)
            if player_hit and effect not in player_hit.status_effects:
                player_hit.status_effects.append(effect)
                print(f"{player_hit.name} is cursed with {effect.upper()} from BLOODLUST!")

        elif creature.rage_type == "feast":
            if player_hit and player_hit.health <= 0:
                heal = int(creature.max_health * 0.1)
                creature.health = min(creature.max_health, creature.health + heal)
                print(f"{creature.name} FEASTS on the fallen, healing {heal} HP!")



    def generate_raid_boss(self, boss_data, biome="Special", difficulty="normal"):
        """Generate a Raid Boss and its minions."""

        raid_boss = Creature(
            boss_data["name"],
            boss_data["abbreviation"],
            biome,
            boss_data["damage"],
            boss_data["health"],
            boss_data["drops"],
            boss_data["exp_range"],
            boss_data["is_predator"],
            boss_data["status_effects"],
            boss_data["special_ability"],
            boss_data["luck"],
            is_raid_boss=True 
        )
        raid_boss.reset_health()

        minions = []

        # Adjust minion count by difficulty
        if difficulty == "easy":
            minion_count = 1
        elif difficulty == "hard":
            minion_count = 3
        else:
            minion_count = random.randint(2, 3)

        for _ in range(minion_count):
            minion_name = random.choice(boss_data["minions"])
            found = False

            for creature in self.creature_templates:
                if creature.name == minion_name:
                    minion = Creature(
                        creature.name,
                        creature.abbreviation,
                        biome,
                        creature.damage,
                        creature.health,
                        creature.drops,
                        creature.exp_range,
                        creature.is_predator,
                        creature.status_effects.copy(),
                        creature.special_ability,
                        creature.luck
                    )
                    minion.reset_health()
                    minions.append(minion)
                    found = True
                    break

            if not found:
                print(f"WARNING: Minion '{minion_name}' could not be found! Creating dummy.")
                dummy = Creature(minion_name, minion_name.lower(), biome, 10, 10, {}, (0, 0), True, [], None, 5)
                dummy.reset_health()
                minions.append(dummy)

        return minions + [raid_boss]



    def display_header(title):
        print("\n╔════════════════════════════════════════════════════════╗")
        print(title.center(50))
        print("╚════════════════════════════════════════════════════════╝")

    def health_bar(current, max_health, width=20):
        filled = int(width * current / max_health)
        return "[" + "#" * filled + "-" * (width - filled) + "]"

    def display_health(entity):
        print(f"{entity.name}: {health_bar(entity.health, entity.max_health)} {entity.health}/{entity.max_health} HP")

    def log_action(action_text):
        print(f"\n>> {action_text}")

    def log_drops(drops):
        print("\n--- Drops Gained ---")
        if drops:
            for item, qty in drops.items():
                print("")
        else:
            print("")

    def log_exp(exp):
        print("")

    def log_item_use(user, target, item, effect):
        print("\n--- Item Use ---")
        print(f"{user.name} uses {item.name} on {target.name} -> {effect}")

    # Register helpers globally so class methods can use them
    globals().update({
        "display_header": display_header,
        "health_bar": health_bar,
        "display_health": display_health,
        "log_action": log_action,
        "log_drops": log_drops,
        "log_exp": log_exp,
        "log_item_use": log_item_use
    })
    def apply_temp_boost(self, player, stat_type, amount, duration):
        """Apply a temporary stat boost to a player"""
        self.temp_boosts[player.name][stat_type] += amount
        self.temp_boosts[player.name]['turns_remaining'] = duration

        # Apply the boost
        if stat_type == 'damage':
            player.damage += amount
        elif stat_type == 'protection':
            player.protection += amount

    def update_temp_boosts(self):
        """Update temporary stat boosts at the end of each turn"""
        for player_name, boosts in self.temp_boosts.items():
            if boosts['turns_remaining'] > 0:
                boosts['turns_remaining'] -= 1

                # Remove expired boosts
                if boosts['turns_remaining'] == 0:
                    player = next(p for p in self.players if p.name == player_name)
                    player.damage -= boosts['damage']
                    player.protection -= boosts['protection']
                    boosts['damage'] = 0
                    boosts['protection'] = 0

    def choose_target(self, for_heal=False):
        """
        Let the player choose a target (creature or player)
        for_heal: if True, only show creatures that are alive
        """
        if for_heal:
            # For healing abilities, show only alive players
            valid_targets = [p for p in self.players if p.health > 0]
        else:
            # For attacks/other abilities, show the current creature
            valid_targets = [c for c in self.creatures if c.health > 0 and not c.escaped] if self.current_creature_index < len(self.creatures) else []

        if not valid_targets:
            print("No valid targets available!")
            return None

        print("\nChoose a target:")
        for i, target in enumerate(valid_targets, 1):
            if isinstance(target, PlayerCharacter):
                print(f"{i}. {target.name} (HP: {target.health}/{target.max_health})")
            else:
                print(f"{i}. {target.name} (HP: {target.health}/{target.max_health})")

        try:
            choice = int(input("Enter target number: ")) - 1
            if 0 <= choice < len(valid_targets):
                return valid_targets[choice]
            else:
                print("Invalid target selection.")
                return None
        except ValueError:
            print("Please enter a valid number.")
            return None

    def parse_inventory(inventory_str):
        return [item.strip() for item in inventory_str.split(',') if item.strip()]
        
    def handle_manual_knockout_drops(self, player):
        inventory_input = input(f"Enter {player.name}'s inventory (comma-separated): ").strip()
        inventory = [item.strip() for item in inventory_input.split(',') if item.strip()]

        if not inventory:
            print(f"No inventory entered for {player.name}.")
            return

        print(f"\nInput Inventory for {player.name}: {', '.join(inventory)}")
        print("")

        # Roll 3 times (duplicates allowed)
        drops = []
        for _ in range(3):
            selected = random.choice(inventory)
            if selected not in drops:
                drops.append(selected)
            if len(drops) == 2:
                break

        print(f"Player dropped these:")
        print("")
        for item in drops:
            if 'X' in item:
                base, count = item.rsplit('X', 1)
                try:
                    count = int(count)
                    drop = f"{base}X1"
                except:
                    drop = item
            else:
                drop = item
            print(f"🗑️  {drop}")

    def sparring_match(self):
        if len(self.players) < 2:
            print("Not enough players to spar!")
            return

        print("\n=== SPARRING MATCH ===")
        print("Available fighters:")
        for i, player in enumerate(self.players, 1):
            print(f"{i}. {player.name}")

        try:
            p1_index = int(input("\nChoose Player 1 (enter number): ")) - 1
            p2_index = int(input("Choose Player 2 (enter number): ")) - 1

            player1 = self.players[p1_index]
            player2 = self.players[p2_index]

            if player1 == player2:
                print("You can't spar against yourself!")
                return

        except (ValueError, IndexError):
            print("Invalid selection.")
            return

        print(f"\n ⚔️ {player1.name} and {player2.name} prepare to spar! ⚔️\n")

        # Save original health
        p1_original_health = player1.health
        p2_original_health = player2.health

        # Start sparring loop
        turn = 0
        while player1.health > 0 and player2.health > 0:
            attacker = player1 if turn % 2 == 0 else player2
            defender = player2 if turn % 2 == 0 else player1

            damage = attacker.damage
            defender.health -= damage
            display_header(attacker.name + "'s Turn")
            print(f">> {attacker.name} strikes {defender.name} for {damage} damage! ({defender.health}/{defender.max_health} HP left)")

            if defender.health <= 0:
                print(f"\n{defender.name} falls! 🏆 {attacker.name} 🏆 wins the sparring match!")
                break

            if input("\nContinue sparring? (y/n): ").lower() != 'y':
                print(">> The sparring match ends in a draw.")
                break

            turn += 1

        # Restore health after spar
        player1.health = p1_original_health
        player2.health = p2_original_health

        print(f"\n{attacker.name} GIVES UP!! {defender.name} WINS!")
        print("=== SPARRING MATCH ENDED ===")
            # 🔧 PATCHED FUNCTIONS (HUNTING DIFFICULTY TUNING) 🔧

            # Updated run_hunting_minigame with stamina + counterattack + better flee + player stats display
    def _convert_biome_name(self, name_or_abbr):
        abbr_map = {
            "wp": "Whispering Pines",
            "cg": "Cinderglen",
            "hr": "Howler's Rise",
            "dl": "Deadlands",
            "bb": "Blacktide Beach"
        }
        return abbr_map.get(name_or_abbr.lower(), name_or_abbr)
    def run_hunting_minigame(self, player, prey, biome):
        import time
        turn = 1
        flee_chance = 0.15
        block_success = False

        print(f"\n🌾 {player.name} begins stalking the {prey.name}...")
        print(f"{prey.name} HP: {prey.health}/{prey.max_health}")
        print(f"{player.name} HP: {player.health}/{player.max_health} | Stamina: {player.stamina}/{player.max_stamina}")

        while prey.health > 0:
            print(f"\n--- Turn {turn} ---")
            print("1. 🫥 Ambush (High damage, harder to land)")
            print("2. 🐾 Pounce (Balanced attack)")
            print("3. 🚫 Block Escape (Lower chance it flees)")
            print("4. ❌ Give Up")

            choice = input("Your move: ").strip().lower()

            if choice == "4":
                print(f"{player.name} gives up the hunt.")
                return

            elif choice == "1":  # Ambush
                if player.stamina < 2:
                    print(f"{player.name} is too tired to ambush!")
                else:
                    hit_chance = 0.6 + (player.luck - prey.luck) * 0.02
                    if random.random() < hit_chance:
                        damage = player.total_damage + random.randint(5, 10)
                        prey.health -= damage
                        player.stamina -= 2
                        print(f"💥 {player.name} ambushes and hits for {damage}!")
                    else:
                        print("❌ The ambush fails. The prey darts away.")
                        retaliation = prey.damage if hasattr(prey, 'damage') else 1
                        player.health -= retaliation
                        print(f"🩸 {prey.name} retaliates and hits {player.name} for {retaliation} damage!")

            elif choice == "2":  # Pounce
                if random.random() < 0.8:
                    damage = player.total_damage
                    prey.health -= damage
                    print(f"✅ {player.name} pounces and deals {damage} damage!")
                else:
                    print("❌ The pounce misses!")
                    retaliation = prey.damage if hasattr(prey, 'damage') else 1
                    player.health -= retaliation
                    print(f"🩸 {prey.name} retaliates and hits {player.name} for {retaliation} damage!")

            elif choice == "3":  # Block Escape
                block_success = True
                print(f"🛑 {player.name} tries to block the prey's escape!")

            else:
                print("Invalid choice. Try 1-4.")
                continue

            # Display updated stats
            print(f"{prey.name} HP: {prey.health}/{prey.max_health}")
            print(f"{player.name} HP: {player.health}/{player.max_health} | Stamina: {player.stamina}/{player.max_stamina}")

            # Check if prey is defeated
            if prey.health <= 0:
                print(f"\n🏁 {player.name} catches the {prey.name}!")
                print("\n=== PLAYER STATS ===")
                print(f"Name:         {player.name}")
                print(f"Max Health:   {player.max_health}")
                print(f"Health:       {player.health}")
                print(f"Max Stamina:  {player.max_stamina}")
                print(f"Stamina:      {player.stamina}")
                print(f"Luck:         {player.luck}")
                print(f"Protection:   {player.protection}")
                print(f"Light:        {player.light}")
                print(f"Damage:       {player.damage}")
                print(f"Status:       {player.status_effects}")
                print("====================\n")
                
                print(f"\n=== PLAYER LINE ===")
                print(player.to_line())
                print(f"=== PLAYER LINE ===\n")


                drops, exp_gained = prey.generate_drops()
                print(f"Drops gained: {drops}")

                for item, quantity in drops.items():
                    self.total_drops[item] = self.total_drops.get(item, 0) + quantity
                self.total_exp += exp_gained
                self._maybe_trigger_posthunt_encounter(biome)

                return

            # Attempt prey escape
            escape_chance = 0.25
            if prey.health < prey.max_health * 0.3:
                escape_chance += 0.3

            if block_success:
                escape_chance -= 0.2

            if random.random() < escape_chance:
                print(f"⚠️ The {prey.name} flees successfully!")
                
                print("\n=== PLAYER STATS ===")
                print(f"Name:         {player.name}")
                print(f"Max Health:   {player.max_health}")
                print(f"Health:       {player.health}")
                print(f"Max Stamina:  {player.max_stamina}")
                print(f"Stamina:      {player.stamina}")
                print(f"Luck:         {player.luck}")
                print(f"Protection:   {player.protection}")
                print(f"Light:        {player.light}")
                print(f"Damage:       {player.damage}")
                print(f"Status:       {player.status_effects}")
                print("====================\n")
                
                print(f"\n=== PLAYER LINE ===")
                print(player.to_line())
                print(f"=== PLAYER LINE ===\n")
                self._maybe_trigger_posthunt_encounter(biome)


                return
            else:
                print(f"⚠️ The {prey.name} tries to flee... but fails.")

            turn += 1

    def _maybe_trigger_posthunt_encounter(self, biome):
        if biome not in self.gathering_encounter_chances:
            return

        chance = self.gathering_encounter_chances[biome]
        if random.random() < chance:
            creatures = [c for c in self.creature_templates if c.biome == biome]
            num_creatures = random.randint(1, 2)

            self.creatures = []
            predators = [c for c in creatures if c.is_predator]
            for creature in random.choices(predators, k=num_creatures):
                new_creature = Creature(
                    creature.name,
                    creature.abbreviation,
                    creature.biome,
                    creature.damage,
                    creature.health,
                    creature.drops,
                    creature.exp_range,
                    creature.is_predator,
                    creature.status_effects.copy(),
                    creature.special_ability,
                    creature.luck
                )
                new_creature.reset_health()
                self.creatures.append(new_creature)

            # Display encounter message
            print("\n" * 3)
            print("\n=== ⚠ ENCOUNTER ⚠ ===\n")
            encounter_counts = {}
            for creature in self.creatures:
                encounter_counts[creature.name] = encounter_counts.get(creature.name, 0) + 1
            print("After the hunt, you've encountered: " +
                  ", ".join(f"{v} {k}" for k, v in encounter_counts.items()) + "!\n")
            print("\n=== ⚠ ENCOUNTER ⚠ ===\n")
            self.start_battle()




    def spawn_raid_boss(self, biome):
        """Spawn a special Raid Boss for investigations."""
        boss_data = random.choice(self.RAID_BOSSES)
        self.creatures = self.generate_raid_boss(boss_data, biome)

        print("\n=== ⚔️ RAID BOSS ENCOUNTER ⚔️ ===")
        print(f"A monstrous creature, {boss_data['name']}, has appeared with its minions!")
        for c in self.creatures:
            print(f"- {c.name} ({c.health} HP)")

        self.start_battle()

    def start_raid_boss_battle(self):
        print("\n=== RAID BOSSES ===")
        for boss in self.RAID_BOSSES:
            print(f"{boss['abbreviation']}: {boss['name']}")

        abbrev = input("Enter the abbreviation of the Raid Boss to fight: ").strip().upper()
        boss_data = next((b for b in self.RAID_BOSSES if b["abbreviation"] == abbrev), None)

        if not boss_data:
            print("Invalid raid boss abbreviation.")
            return

        difficulty = input("Choose difficulty (easy / normal / hard): ").strip().lower()
        if difficulty not in ["easy", "normal", "hard"]:
            difficulty = "normal"

        self.creatures = self.generate_raid_boss(boss_data, "Special", difficulty)

        print("\n" * 21)
        print("💀💀💀 RAID BOSS ENCOUNTER 💀💀💀")
        print(f"{boss_data['name']} appears with minions!")
        for c in self.creatures:
            print(f"- {c.name} ({c.health} HP)")

        self.current_creature_index = 0
        self.start_battle()



    def scout(self):
        if not self.players:
            self.prompt_for_players()
        if not self.players:
            return

        # Select players for investigation
        investigators = []
        print("\n=== INVESTIGATION TEAM SELECTION ===")
        for i, player in enumerate(self.players, 1):
            print(f"{i}. {player.name} (Stamina: {player.stamina}/{player.max_stamina})")

        while True:
            choice = input("\nAdd player to investigation (number) or type 'done' to start: ").strip()
            if choice.lower() == "done":
                if investigators:
                    break
                else:
                    print("You need at least one cat to investigate.")
                    continue

            try:
                idx = int(choice) - 1
                if idx not in range(len(self.players)):
                    print("Invalid number.")
                    continue

                selected = self.players[idx]
                if selected in investigators:
                    print(f"{selected.name} is already in.")
                    continue

                if selected.stamina < 5:
                    print(f"{selected.name} is too tired to investigate.")
                    continue

                investigators.append(selected)
                print(f"{selected.name} joins the investigation.")

            except ValueError:
                print("Invalid input.")

        # Choose biome
        biomes = list(self.biomes.keys())
        print("\n=== CHOOSE BIOME TO INVESTIGATE ===")
        for i, biome in enumerate(biomes, 1):
            print(f"{i}. {biome}")

        while True:
            try:
                biome_choice = int(input("Enter biome number: ")) - 1
                if biome_choice not in range(len(biomes)):
                    print("Invalid.")
                    continue
                biome = biomes[biome_choice]
                break
            except ValueError:
                print("Invalid input.")

        # Spend stamina
        for p in investigators:
            p.stamina -= 5

        print(f"\n>> The team heads to {biome} to investigate...")

        roll = random.randint(1, 10)

        if roll <= 3:
            print("\n>> Nothing found. The area is calm.")
            return

        elif roll <= 6:
            print("\n>> Signs of past trouble, but no danger now.")
            print(">> The scents are old. Nothing is here anymore, but your team feels more cautious. +10 Stamina")

            for p in investigators:
                p.stamina += 10  # +1 stamina back as they didn't waste energy
            return


        elif roll <= 8:
            print("\n>> Ambushed during investigation!")

            possible_enemies = [c for c in self.creature_templates if c.biome == biome and c.is_predator]

            # If no predators available, fallback to prey
            if not possible_enemies:
                possible_enemies = [c for c in self.creature_templates if c.biome == biome]

            num_creatures = random.randint(1, 2)

            self.creatures = []
            for _ in range(num_creatures):
                enemy = random.choice(possible_enemies)
                new_creature = Creature(
                    enemy.name,
                    enemy.abbreviation,
                    enemy.biome,
                    enemy.damage,
                    enemy.health,
                    enemy.drops,
                    enemy.exp_range,
                    enemy.is_predator,
                    enemy.status_effects.copy(),
                    enemy.special_ability,
                    enemy.luck
                )
                new_creature.reset_health()
                self.creatures.append(new_creature)

            print("\n>> Hostiles approach!")
            for creature in self.creatures:
                print(f"- {creature.name} ({creature.health} HP)")

            self.start_battle()
            return

        else:
            print("\n>> YOU FOUND THEM. A raid is preparing in the shadows!")
            print(">> A monstrous creature will soon attack!")

            # Spawn raid boss + minions
            self.spawn_raid_boss(biome)

    def shadow_lottery(self):
        lottery = ShadowLottery()
        print("\n" * 21)
        print("🎲 === SHADOW LOTTERY ===")
        print("How many draws would you like?")

        try:
            num_draws = int(input("Enter number of draws: "))
            if num_draws < 1:
                print("⚠️ Must draw at least once!")
                return

            results = lottery.draw_lottery(num_draws)

            print("\n" * 21)
            print("# 🎉 === LOTTERY RESULTS ===")
            for i, result in enumerate(results, 1):
                print(f"Item Won: {result['item']}")
                print("")
            print("\n🎲 === END OF LOTTERY ===\n")

        except ValueError:
            print("❌ Invalid input! Please enter a number.")


        except ValueError:
            print("Please enter a valid number")

        # Add new method to Battle class
    def gather_plants(self, player):
        # Check stamina first
        stamina_cost = 2
        if player.stamina < stamina_cost:
            print(f"Not enough stamina to gather plants. Required: {stamina_cost}")
            return

        # Keep asking for biome until valid
        while True:
            current_biome = input("Which biome are you gathering in?: ").strip().capitalize()
            full_biome = None
            for biome, abbrev in BIOME_ABBREVIATIONS.items():
                if current_biome.upper() == abbrev or current_biome.lower() == biome.lower():
                    full_biome = biome
                    break

            if full_biome and full_biome in self.biomes:
                break
            print("Invalid biome selected. Please try again.")

        # Define plants available in each biome
        biome_plants = {
            "Howler's Rise": {
                "Comfrey Root": 0.7,
                "Goldenrod": 0.7,
                "Poppy Seeds": 0.7,
                "Horsetail": 0.3,
                "Rock": 0.5,
                "Antler": 0.3,
                "Root": 0.4
            },
            "Whispering Pines": {
                "Burdock Root": 0.5,
                "Dock Leaves": 0.4,
                "Juniper Berries": 0.7,
                "Marigold": 0.7,
                "Grass": 0.3,
                "Stick": 0.6,
                "Sap": 0.5,
                "Moss": 0.4,
                "Pinecone": 0.5
            },
            "Cinderglen": {
                "Blackberry Leaves": 0.5,
                "Catmint": 0.7,
                "Dock Leaves": 0.8,
                "Grass": 0.3,
                "Thistle Patches": 0.6,
                "Stone": 0.6
            },
            "Deadlands": {
                "Shard": 0.3
            },
            "Blacktide Beach": {
                "Seaweed": 0.8
            }
        }

        # Let player choose a plant
        while True:
            plant_choice = input("\nEnter the name or abbreviation of the plant you want to gather: ").strip()
            selected_plant = None

            for plant in biome_plants[full_biome].keys():
                if (plant_choice.lower() == plant.lower() or 
                    plant_choice.upper() == PLANT_ABBREVIATIONS.get(plant, "")):
                    selected_plant = plant
                    break

            if selected_plant:
                break
            print("Invalid plant selection. Please try again.")
        chance = biome_plants[full_biome][selected_plant]
        player.stamina -= stamina_cost

        if random.random() < chance:
            amount = random.randint(1, 3)
            print("")
            print("")
            print("\n=== 🌿 GATHERING RESULT 🌿 ===")
            print(f"\nSuccess! You gathered {amount} {selected_plant}(s)")
            print("\n=== 🌿 GATHERING RESULT 🌿 ===")
            print("")
            print("")

            print("\n=== PLAYER STATS ===")
            print(f"Name:         {player.name}")
            print(f"Max Health:   {player.max_health}")
            print(f"Health:       {player.health}")
            print(f"Max Stamina:  {player.max_stamina}")
            print(f"Stamina:      {player.stamina}")
            print(f"Luck:         {player.luck}")
            print(f"Protection:   {player.protection}")
            print(f"Light:        {player.light}")
            print(f"Damage:       {player.damage}")
            print(f"Status:       {player.status_effects}")
            print("====================\n")
            
            print(f"\n=== PLAYER LINE ===")
            print(player.to_line())
            print(f"=== PLAYER LINE ===\n")

        else:
            print("\n=== PLAYER STATS ===")
            print(f"Name:         {player.name}")
            print(f"Max Health:   {player.max_health}")
            print(f"Health:       {player.health}")
            print(f"Max Stamina:  {player.max_stamina}")
            print(f"Stamina:      {player.stamina}")
            print(f"Luck:         {player.luck}")
            print(f"Protection:   {player.protection}")
            print(f"Light:        {player.light}")
            print(f"Damage:       {player.damage}")
            print(f"Status:       {player.status_effects}")
            print("====================\n")
            print("")
            print("")
            print("\n=== 🌿 GATHERING RESULT 🌿 ===")
            print(f"\nFailed to gather {selected_plant}")
            print("\n=== 🌿 GATHERING RESULT 🌿 ===")
            print("")
            print("")
            print(f"\n=== PLAYER LINE ===")
            print(player.to_line())
            print(f"=== PLAYER LINE ===\n")

        # Inside gather_plants method, replace the creature encounter section with:
        if random.random() < self.gathering_encounter_chances[full_biome]:
            creatures = [c for c in self.creature_templates if c.biome == full_biome]
            num_creatures = random.randint(1, 2)

            # Create the creature instances
            self.creatures = []
            predators = [c for c in creatures if c.is_predator]
            for creature in random.choices(predators, k=num_creatures):
                new_creature = Creature(
                    creature.name,
                    creature.abbreviation,
                    creature.biome,
                    creature.damage,
                    creature.health,  # This sets both health and max_health
                    creature.drops,
                    creature.exp_range,
                    creature.is_predator,
                    creature.status_effects.copy(),  # Make a copy of status effects
                    creature.special_ability,  # ← ADD THIS
                    creature.luck  # ← Also make sure luck gets passed properly
                )
                new_creature.reset_health()  # Explicitly reset health
                self.creatures.append(new_creature)

            # Display encounter message with specific details
            creature_counts = {}
            for creature in self.creatures:
                creature_counts[creature.name] = creature_counts.get(creature.name, 0) + 1

            # Clear screen and display formatted encounter message
            print("\n" * 3)  # Print 21 empty lines to clear screen
            print("\n=== ⚠ ENCOUNTER ⚠ ===")
            print("")
            encounter_message = "While gathering, you've encountered: "
            encounter_details = [f"{count} {name}" for name, count in creature_counts.items()]
            print(encounter_message + ", ".join(encounter_details) + "!")
            print("")
            print("\n=== ⚠ ENCOUNTER ⚠ ===")

            self.start_battle()

    def prompt_for_players(self):
        num_players = int(input("Enter the number of players (0 for none at the beginning): "))
        if num_players > 0:
            for _ in range(num_players):
                player_stats = PlayerCharacter.from_input()
                self.players.append(player_stats)
        else:
            print("No players will be created. Starting with an empty game.")
            return False  # Indicate no players were created
        return True  # Indicate players were created

    def choose_action(self):
        while True:
            print("\n" * 21)
            action = input("What are you doing?").strip().lower()

            if action == 'b':
                if not self.players:  # If no players exist
                    self.prompt_for_players()

                if self.players:  # Proceed with battle if players exist
                    self.initiate_battle()
                    continue  # Continue the loop for the next action
            elif action == 'spar':
                if not self.players:
                    self.prompt_for_players()
                if self.players:
                    self.sparring_match()
                continue

    # Add to existing choose_action method
            elif action == 'f':
                farming = FarmingSystem()
                while True:
                    print("\n" * 10)
                    print("\n=== FARMING MENU ===")
                    print("1. Plant and harvest crop")
                    print("2. Exit farming")

                    choice = input("Choose an option: ")

                    if choice == "1":
                        farming.plant_and_harvest()
                    elif choice == "2":
                        break
                    else:
                        print("Invalid choice!")
            elif action == 'rb':
                if not self.players:
                    self.prompt_for_players()
    
                if self.players:
                    print("\n=== RAID BOSS BATTLE ===")
                    print("You have chosen to face a Raid Boss manually!")
                    self.start_raid_boss_battle()
                continue


            elif action == 's':
                if not self.players:
                    self.prompt_for_players()
                if self.players:
                    battle.sell_items(ITEM_VALUES)
                continue

            elif action == 'r':
                if not self.players:
                    self.prompt_for_players()

                if self.players:
                    self.recover_menu(self.players[0])
                    continue

            elif action == 'l':
                self.shadow_lottery()
                continue

            elif action == 't':
                if not self.players:  # If no players exist
                    self.prompt_for_players()

                if self.players:  # Proceed with travel if players exist
                    self.travel(self.players[0])  # Assuming you want to travel with the first player
                    continue  # Continue the loop for the next action

            elif action == 're':
                print("Refreshing the game...")
                self.players.clear()  # Clear all players
                self.creatures.clear()  # Clear all creatures
                self.current_creature_index = 0  # Reset creature index
                self.total_drops.clear()  # Clear drops
                self.total_exp = 0  # Reset experience
                self.prompt_for_players()  # Start fresh with new players
                continue

            elif action == 'g':
                if not self.players:
                    self.prompt_for_players()
                if self.players:  # Only proceed if there are players
                    self.gather_plants(self.players[0])  # Use the first player for gathering
                continue
            elif action == "h":
                if not self.players:
                    self.prompt_for_players()
                if self.players:
                    current_biome = input("Which biome are you hunting in?: ").strip().capitalize()
                    full_biome = None
                    for biome, abbrev in BIOME_ABBREVIATIONS.items():
                        if current_biome.upper() == abbrev or current_biome.lower() == biome.lower():
                            full_biome = biome
                            break

                    if not full_biome or full_biome not in self.biomes:
                        print("Invalid biome selected. Please try again.")
                
                    prey_input = input("🎯 Enter the abbreviation of the prey you want to hunt: ").strip().lower()
            
                    # Search directly in creature_templates for prey matching the abbreviation
                    selected_prey = next(
                        (prey for prey in self.creature_templates if prey.is_prey() and prey.abbreviation.lower() == prey_input),
                        None
                    )
            
                    if selected_prey:
                        # 👤 Prompt for who is doing the action
                        print("\n👤 Who is hunting?")
                        for idx, player in enumerate(self.players, 1):
                            print(f"{idx}. {player.name}")
            
                        try:
                            choice = int(input("Enter number: ")) - 1
                            if 0 <= choice < len(self.players):
                                player = self.players[choice]
                            else:
                                print("Invalid choice. Defaulting to first player.")
                                player = self.players[0]
                        except ValueError:
                            print("Invalid input. Defaulting to first player.")
                            player = self.players[0]

                
            
                        self.run_hunting_minigame(player, selected_prey, full_biome)
                    else:
                        print("❌ No prey found with that abbreviation. Please try again.")
                continue


                
            elif action == "kymera":
                shop = KymeraDynamicShop(ITEM_VALUES)
                print(shop.generate_shop())
                continue

            elif action == 'c':
                if not self.players:
                    self.prompt_for_players()

                if self.players:
                    self.craft_menu(self.players[0])
                continue

            elif action == 'bo':
                self.show_bounties()
                continue
            elif action == "pa":
                self.patrol()
                continue
            elif action == "sc":
                self.scout()
                continue


            else:
                print("Invalid action. Try again.")

    def travel(self, player):
        """Handle multiple players traveling from one biome to another using full names or abbreviations."""
        # Get starting biome
        start_input = input("Which territory are you leaving? (name or abbreviation): ").strip()
        starting_biome = None

        # Check for both full name and abbreviation
        for biome, abbrev in BIOME_ABBREVIATIONS.items():
            if start_input.upper() == abbrev or start_input.lower() == biome.lower():
                starting_biome = biome
                break

        if not starting_biome or starting_biome not in self.biomes:
            print("Invalid territory. Please choose a valid starting point.")
            return

        # Get destination biome
        dest_input = input("Where are you traveling to? (name or abbreviation): ").strip()
        destination_biome = None

        # Check for both full name and abbreviation
        for biome, abbrev in BIOME_ABBREVIATIONS.items():
            if dest_input.upper() == abbrev or dest_input.lower() == biome.lower():
                destination_biome = biome
                break

        if not destination_biome or destination_biome not in self.biomes:
            print("Invalid destination territory. Please select a valid destination.")
            return

        stamina_cost = self.travel_costs.get((starting_biome, destination_biome))
        if stamina_cost is None:
            print(f"You cannot travel directly from {starting_biome} to {destination_biome}.")
            return

        # Check if all players have enough stamina
        for player in self.players:
            if player.stamina < stamina_cost:
                print("\n" * 21)
                print(f"{player.name} is too tired to travel to {destination_biome}.")
                return

        # If we get here, all players have enough stamina, so deduct it
        for player in self.players:
            player.stamina -= stamina_cost
            player.rest_counter = 0
            print("\n" * 21)
            print("\n====== TRAVEL SUMMARY ======")
            print(f"{player.name} travels swiftly from {starting_biome} to {destination_biome} and it takes {stamina_cost} stamina.")

            print("\n=== PLAYER STATS ===")
            print(f"Name:         {player.name}")
            print(f"Max Health:   {player.max_health}")
            print(f"Health:       {player.health}")
            print(f"Max Stamina:  {player.max_stamina}")
            print(f"Stamina:      {player.stamina}")
            print(f"Luck:         {player.luck}")
            print(f"Protection:   {player.protection}")
            print(f"Light:        {player.light}")
            print(f"Damage:       {player.damage}")
            print(f"Status:       {player.status_effects}")
            print("====================\n")
            
            print(f"\n=== PLAYER LINE ===")
            print(player.to_line())
            print(f"=== PLAYER LINE ===\n")

        encounter_chance = random.randint(1, 100)

        if encounter_chance <= 25:

            # PREVENT STORM if it would drop a player below 0
            for player in self.players:
                if player.stamina - 10 < 0:
                    print(f"\n🌩️ A storm brews... but {player.name} is too exhausted to continue.")
                    print(f"{player.name} collapses from exhaustion! The group must stop traveling!")
                    print("")
                    print("\n=== PLAYER STATS ===")
                    print(f"Name:         {player.name}")
                    print(f"Max Health:   {player.max_health}")
                    print(f"Health:       {player.health}")
                    print(f"Max Stamina:  {player.max_stamina}")
                    print(f"Stamina:      {player.stamina}")
                    print(f"Luck:         {player.luck}")
                    print(f"Protection:   {player.protection}")
                    print(f"Light:        {player.light}")
                    print(f"Damage:       {player.damage}")
                    print(f"Status:       {player.status_effects}")
                    print("====================\n")
                    
                    print(f"\n=== PLAYER LINE ===")
                    print(player.to_line())
                    print(f"=== PLAYER LINE ===\n")
                    return

            print("\nThe storm hits! Everyone loses 10 stamina.")
            for player in self.players:
                player.stamina -= 10
                player.clamp_stats()
                print("\n=== PLAYER STATS ===")
                print(f"Name:         {player.name}")
                print(f"Max Health:   {player.max_health}")
                print(f"Health:       {player.health}")
                print(f"Max Stamina:  {player.max_stamina}")
                print(f"Stamina:      {player.stamina}")
                print(f"Luck:         {player.luck}")
                print(f"Protection:   {player.protection}")
                print(f"Light:        {player.light}")
                print(f"Damage:       {player.damage}")
                print(f"Status:       {player.status_effects}")
                print("====================\n")
                
                print(f"\n=== PLAYER LINE ===")
                print(player.to_line())
                print(f"=== PLAYER LINE ===\n")

        elif encounter_chance <= 50:
            event_type = random.choice(["cache", "healer"])
            if event_type == "cache":

                print("\n=== PLAYER STATS ===")
                print(f"Name:         {player.name}")
                print(f"Max Health:   {player.max_health}")
                print(f"Health:       {player.health}")
                print(f"Max Stamina:  {player.max_stamina}")
                print(f"Stamina:      {player.stamina}")
                print(f"Luck:         {player.luck}")
                print(f"Protection:   {player.protection}")
                print(f"Light:        {player.light}")
                print(f"Damage:       {player.damage}")
                print(f"Status:       {player.status_effects}")
                print("====================\n")
                
                print(f"\n=== PLAYER LINE ===")
                print(player.to_line())
                print(f"=== PLAYER LINE ===\n")

                print("💸 While traveling, your group uncovers a cleverly hidden stash left by another clan! Everyone receives a surprise prize. 💸")
            elif event_type == "healer":
                print("\n🌿 You meet a traveling medicine cat who treats your wounds and replenishes your energy!")
                
                for player in self.players:
                    player.health = player.max_health
                    player.stamina = player.max_stamina

                    # Show updated line and stats
                    print(f"\n=== PLAYER LINE ===")
                    print(player.to_line())
                    print("=== PLAYER LINE ===")

                    print("\n=== PLAYER STATS ===")
                    print(f"Name:         {player.name}")
                    print(f"Max Health:   {player.max_health}")
                    print(f"Health:       {player.health}")
                    print(f"Max Stamina:  {player.max_stamina}")
                    print(f"Stamina:      {player.stamina}")
                    print(f"Luck:         {player.luck}")
                    print(f"Protection:   {player.protection}")
                    print(f"Light:        {player.light}")
                    print(f"Damage:       {player.damage}")
                    print(f"Status:       {player.status_effects}")
                    print("====================\n")
        else:
            self.creatures.clear()
            self.current_creature_index = 0  # Reset the creature index
            creatures = self.biomes[destination_biome]
            num_creatures = random.randint(1, 3)

            self.creatures = []
            predators = [c for c in self.creature_templates if c.biome == destination_biome and c.is_predator]

            for creature in random.choices(predators, k=num_creatures):
                new_creature = Creature(
                    creature.name,
                    creature.abbreviation,
                    creature.biome,
                    creature.damage,
                    creature.health,
                    creature.drops,
                    creature.exp_range,
                    creature.is_predator,
                    creature.status_effects.copy(),
                    creature.special_ability,  # ← ADD THIS
                    creature.luck 
                )
                new_creature.reset_health()
                self.creatures.append(new_creature)

            print(f"\n⚠ During travel, the group encountered {len(self.creatures)} creatures! ⚠")
            for creature in self.creatures:
                print(f" → {creature.name}")
            self.start_battle()

    def join_new_player(self):
        """Handle the joining of a new player during the battle."""
        print("")
        print("")
        print("")
        print("\n--- A new player wants to join the battle! ---")
        new_player = PlayerCharacter.from_input()  # Create a new player character
        self.players.append(new_player)  # Add to the existing list of players
        print(f"{new_player.name} has joined the battle!")
        print("\n---                                        ---")

    def roar_of_need(self, player):
        # Get the current player (assuming it's the first player's turn)
        if player.stamina >= 10:
            player.stamina -= 10
            new_player = PlayerCharacter.from_input()  # Create a new player character
            self.players.append(new_player)  # Add to the existing list of players
            print(f"{new_player.name} has joined the battle!")
            print("\n---                                        ---")
        else:
            print(f"Not enough stamina! Required: 10, Current: {current_player.stamina}")

    def initiate_battle(self):
        creature_abbrev = input("Enter the abbreviation of the creature to battle: ").strip().upper()

        selected_creature = next((c for c in self.creature_templates if c.abbreviation.lower() == creature_abbrev.lower()), None)
        if not selected_creature:
            print("Invalid creature abbreviation.")
            return

        while True:
            print("")
            choice = input("Would you like to (R)oll for a random number of enemies (1-4) or (C)hoose how many? ").strip().lower()
            if choice == 'r':
                num_creatures = random.randint(1, 4)
                break
            elif choice == 'c':
                try:
                    print("")
                    num_creatures = int(input("Enter how many enemies to fight: ").strip())
                    if num_creatures > 0:
                        break
                    else:
                        print("Please enter a number between 1 and 10.")
                except ValueError:
                    print("Invalid number. Try again.")
            else:
                print("Please enter R for random or C to choose.")

        self.creatures = [
            Creature(
                selected_creature.name,
                selected_creature.abbreviation,
                selected_creature.biome,
                selected_creature.damage,
                selected_creature.max_health,
                selected_creature.drops,
                selected_creature.exp_range,
                selected_creature.is_predator,
                selected_creature.status_effects,
                selected_creature.special_ability,
                selected_creature.luck
            ) for _ in range(num_creatures)
        ]

        print("\n" * 21)
        print("\n--- 🐾 CREATURE(S) ENCOUNTERED 🐾 ---")
        print(f"You will face ⚠️ {num_creatures} {selected_creature.name}(s) ⚠️!")
        for creature in self.creatures:
            print(f"- {creature}")

        self.current_creature_index = 0
        self.start_battle()


    def check_battle_end_conditions(self):
        if all(p in self.escaped_players for p in self.players):
            print("All players have escaped! Ending the battle.")
            return True
        elif all(p.health <= 0 for p in self.players):
            print("All players have been defeated!")
            return True
        return False

    def end_battle(self):
        for player in self.players:
            player.clear_temp_stats()
            player.rest_counter = 0

        for player_name, boosts in self.temp_boosts.items():
            if boosts['damage'] > 0 or boosts['protection'] > 0:
                player = next(p for p in self.players if p.name == player_name)
                player.damage -= boosts['damage']
                player.protection -= boosts['protection']
                boosts['damage'] = 0
                boosts['protection'] = 0
                boosts['turns_remaining'] = 0

        print("\n========== BATTLE SUMMARY ==========")

        for player in self.players:
            print("")
            print(f"\n=== PLAYER LINE ===")
            print(player.to_line())
            print(f"=== PLAYER LINE ===\n")

            print("")
            print(f"\n--- {player.name}'s Final Stats ---")
            print(f"Health     : {player.health}/{player.max_health}")
            print(f"Stamina    : {player.stamina}/{player.max_stamina}")
            print(f"Damage     : {player.damage}")
            print(f"Protection : {player.protection}")
            print(f"Luck       : {player.luck}")
            print(f"Light      : {player.light}")
            print(f"Status     : {', '.join(player.status_effects) if player.status_effects else 'None'}")

            if player.health <= 0:
                self.handle_manual_knockout_drops(player)

            # Always remove daze after battle
            if 'daze' in player.status_effects:
                player.status_effects.remove('daze')
                print(f"(Daze effect removed from {player.name})")

        self.distribute_drops_to_players()

        print("\n--- Items Used During Battle ---")
        if self.items_used:
            for item_name, count in self.items_used.items():
                print(f"{item_name}: {count}")
        else:
            print("No items were used.")

        print("\n====================================\n")
            
    def attempt_escape_player(self, player, active_creature):
        if random.random() < 0.4:  # 40% chance to escape
            print(f"\n{player.name} successfully escaped from {active_creature.name}!\n")

            print("====== PLAYER ESCAPE STATS ======")
            print(f"Name       : {player.name}")
            print(f"Health     : {player.health}/{player.max_health}")
            print(f"Stamina    : {player.stamina}/{player.max_stamina}")
            print(f"Damage     : {player.damage}")
            print(f"Protection : {player.protection}")
            print(f"Luck       : {player.luck}")
            print(f"Light      : {player.light}")
            print(f"Status     : {', '.join(player.status_effects) if player.status_effects else 'None'}")
            print("==================================")

            print(f"\n=== PLAYER LINE ===")
            print(player.to_line())
            print(f"=== PLAYER LINE ===\n")


            print(f"\n[ESCAPE SUCCESS] {player.name} has left the battle.")
            return True
        else:
            damage_dealt = max(active_creature.damage - player.protection, 0)
            player.health -= damage_dealt
            print(f"{player.name} failed to escape and takes {damage_dealt} damage from {active_creature.name}!")
            if player.health <= 0:
                print(f"{player.name} has been defeated!")
            return False

    def attempt_escape_creature(self, battle):
        ESCAPE_CHANCE = 0.25 + (self.luck / 100)  # Base 25% + up to +25%
        if self.is_prey() and self.health < self.max_health * 0.6:
            if random.random() < ESCAPE_CHANCE:
                log_action(f"{self.name} panics and flees the battle!")
                battle.creatures.remove(self)
                return True
        return False

        print(f"{player.name} failed to escape and takes {damage_dealt} damage from {active_creature.name}!")
        if player.health <= 0:
            print(f"{player.name} has been defeated!")
        return False  # Return False to indicate the battle continuesrn None

    def show_bounties(self):
        bounty_system = BountySystem(ITEM_VALUES, creature_templates)
        available_bounties = bounty_system.get_available_bounties()
        print("\n" * 21)
        print("\n=== Available Bounties ===")
        for i, bounty in enumerate(available_bounties, 1):
            print(f"\n{i}. {bounty['type']} Bounty:")
            print(f"Task: {bounty['task']}")
            print(f"Reward: {bounty['reward']}")

        choice = input("\nSelect a bounty (1-3) or press Enter to skip: ")
        if choice.isdigit() and 1 <= int(choice) <= len(available_bounties):
            selected_bounty = available_bounties[int(choice)-1]
            print(f"\nYou've accepted the bounty: {selected_bounty['task']}")
            print(f"Complete this task to earn {selected_bounty['reward']}!")
            print("\n===               ===")
            return selected_bounty
        return None

    def reset_all_creatures(self):
        """Reset health for all creatures in the battle."""
        for creature in self.creatures:
            creature.reset_health()
    def patrol(self):
        if not self.players:
            self.prompt_for_players()
        if not self.players:
            return

        # Team selection
        patrol_team = []
        print("\n=== PATROL TEAM SELECTION ===")
        for i, player in enumerate(self.players, 1):
            print(f"{i}. {player.name} (Stamina: {player.stamina}/{player.max_stamina})")

        while True:
            choice = input("\nAdd player to patrol (number) or type 'done' to start patrol: ").strip()
            if choice.lower() == "done":
                if patrol_team:
                    break
                else:
                    print("You need at least one patrol member.")
                    continue

            try:
                idx = int(choice) - 1
                if idx not in range(len(self.players)):
                    print("Invalid number.")
                    continue

                selected = self.players[idx]
                if selected in patrol_team:
                    print(f"{selected.name} is already in.")
                    continue

                if selected.stamina < 5:
                    print(f"{selected.name} has too little stamina (need 5).")
                    continue

                patrol_team.append(selected)
                print(f"{selected.name} joins patrol!")

            except ValueError:
                print("Invalid input.")

        # Spend stamina
        for p in patrol_team:
            p.stamina -= 5

        leader = patrol_team[0]
        print(f"\n>> {leader.name} leads the patrol.")
        print(">> The patrol heads out...")

        # Encounter Roll
        roll = random.randint(1, 10)

        # Slightly safer with more players
        if len(patrol_team) >= 3 and roll == 9:
            roll = 8  # Avoid ambush

        # ==== PEACEFUL ====
        if roll <= 3:
            print("\n>> The patrol is peaceful. You find herbs by a quiet brook.")

            print("Do you...")
            print("1. Gather them quickly (risk getting less)")
            print("2. Gather carefully (takes longer, safer)")
            print("3. Leave them alone")

            choice = input("> Choose: ").strip()

            if choice == "1":
                if random.random() < 0.5:
                    print(">> Herbs gathered successfully!")
                    for p in patrol_team:
                        print(f"{p.name} gains 2x Herbs")
                else:
                    print(">> Herbs withered while rushed. Nothing gained.")

            elif choice == "2":
                print(">> Carefully gathered herbs.")
                for p in patrol_team:
                    print(f"{p.name} gains 3x Herbs")

            else:
                print(">> You leave the herbs untouched.")

        # ==== PREY ====
        elif roll <= 6:
            prey = random.choice(["Mouse", "Squirrel", "Rabbit", "Small Bird"])
            print(f"\n>> You spot a {prey}.")

            print("How do you approach?")
            print("1. Ambush carefully (+bonus if success, harder)")
            print("2. Charge in (easy roll, lower reward)")
            print("3. Ignore")

            choice = input("> Choose: ").strip()

            if choice == "1":
                if random.random() < 0.4:
                    print(">> Perfect ambush! You caught the prey cleanly.")
                    for p in patrol_team:
                        print(f"{p.name} gains 3x Food")
                else:
                    print(">> The prey escaped...")

            elif choice == "2":
                if random.random() < 0.8:
                    print(">> You caught it, but it's small.")
                    for p in patrol_team:
                        print(f"{p.name} gains 1x Food")
                else:
                    print(">> Prey escaped.")

            else:
                print(">> You ignore it and move on.")

        # ==== ENEMY SIGHTING ====
        elif roll <= 8:
            print("\n>> Hostile creature spotted ahead!")

            print("What do you do?")
            print("1. Attack first")
            print("2. Try to sneak by (Luck roll)")
            print("3. Retreat (End patrol safely)")

            choice = input("> Choose: ").strip()

            if choice == "2":
                # Sneak roll
                success = random.random() < 0.4
                if success:
                    print(">> You sneak by successfully. Patrol ends peacefully.")
                    return
                else:
                    print(">> Failed! They spotted you.")

            if choice == "3":
                print(">> You retreat safely.")
                return

            # COMBAT START
            biome = random.choice(list(self.biomes.keys()))
            enemy = random.choice(self.biomes[biome])

            self.creatures = [Creature(
                enemy.name, enemy.abbreviation, enemy.biome, enemy.damage, enemy.health,
                enemy.drops, enemy.exp_range, enemy.is_predator, enemy.status_effects.copy(),
                enemy.special_ability, enemy.luck
            )]

            self.creatures[0].reset_health()
            print(f"\n>> {enemy.name} appears! ({enemy.health} HP)")
            self.start_battle()

        # ==== AMBUSH ====
        elif roll == 9:
            print("\n>> AMBUSH! Enemies surround you.")

            biome = random.choice(list(self.biomes.keys()))
            possible_enemies = [c for c in self.creature_templates if c.biome == biome and c.is_predator]

            # If no predators available, fallback to prey
            if not possible_enemies:
                possible_enemies = [c for c in self.creature_templates if c.biome == biome]
            num_creatures = random.randint(2, 3)

            self.creatures = []
            for _ in range(num_creatures):
                enemy = random.choice(possible_enemies)
                new_creature = Creature(
                    enemy.name, enemy.abbreviation, enemy.biome, enemy.damage, enemy.health,
                    enemy.drops, enemy.exp_range, enemy.is_predator, enemy.status_effects.copy(),
                    enemy.special_ability, enemy.luck
                )
                new_creature.reset_health()
                self.creatures.append(new_creature)

            print("\n>> Enemies charge!")
            for c in self.creatures:
                print(f"- {c.name} ({c.health} HP)")

            self.start_battle()

        # ==== SPECIAL FIND ====
        else:
            print("\n>> You find a hidden cache among rocks!")

            print("Do you...")
            print("1. Grab it fast (risk enemy)")
            print("2. Search carefully (safe)")
            print("3. Leave it")

            choice = input("> Choose: ").strip()

            if choice == "1":
                if random.random() < 0.4:
                    print(">> As you grab it, enemies appear!")
                    biome = random.choice(list(self.biomes.keys()))
                    enemy = random.choice(self.biomes[biome])

                    self.creatures = [Creature(
                        enemy.name, enemy.abbreviation, enemy.biome, enemy.damage, enemy.health,
                        enemy.drops, enemy.exp_range, enemy.is_predator, enemy.status_effects.copy(),
                        enemy.special_ability, enemy.luck
                    )]

                    self.creatures[0].reset_health()
                    self.start_battle()
                else:
                    print(">> You grab rare loot and escape!")
                    for p in patrol_team:
                        print(f"{p.name} gains +1 Luck item")

            elif choice == "2":
                print(">> Carefully gathered cache safely.")
                for p in patrol_team:
                    print(f"{p.name} gains +1 Health item")

            else:
                print(">> Left untouched.")

        # Patrol end summary
        print("\n=== PATROL OVERVIEW ===")
        for p in patrol_team:
            print(f"{p.name},{p.max_health},{p.health},{p.stamina},{p.max_stamina},{p.luck},{p.protection},{p.light},{p.damage},{p.status_effects}")

    def craft_menu(self, player):
        crafting = CraftingSystem()

        while True:
            recipe_name = input("Enter the name of the item to craft or 'exit' to leave: ")
            crafting.craft_item(player, recipe_name, player.inventory)
            if recipe_name == 'exit':
                break

    def recover_menu(self, player):
        """Handle recovery options for the player."""
        while True:
            print("\nRecovery Options:")
            print("1. Nap (Recover 10 stamina)")
            print("2. Sleep (Recover 25 stamina)")
            print("3. Use Item")
            print("4. Back")
            print("5. CREATURE Encounter")
            print("6. Equip/Unequip Armor\n")

            choice = input("Choose an option: ").strip()

            if choice in ['1', '2']:
                nest = player.current_nest
                rest_penalty = player.rest_counter * 3

                # Base values depending on nap/sleep
                if choice == '1':
                    base_stam = 10
                    base_hp = 5
                    action_word = "naps"
                else:
                    base_stam = 25
                    base_hp = 10
                    action_word = "SLEEPS"

                # Adjust based on nest type
                if nest == "Broken Nest":
                    stam_gain = base_stam - rest_penalty
                    hp_gain = base_hp - rest_penalty
                elif nest == "Woven Nest":
                    stam_gain = base_stam + 5 - rest_penalty
                    hp_gain = base_hp + 5 - rest_penalty
                elif nest == "Padded Nest":
                    stam_gain = base_stam + 10 - rest_penalty
                    hp_gain = base_hp + 10 - rest_penalty
                elif nest == "Fortified Den":
                    stam_gain = player.max_stamina
                    hp_gain = 25
                    player.rest_counter = 0
                elif nest == "Luxury Hollow":
                    stam_gain = player.max_stamina
                    hp_gain = player.max_health
                    player.rest_counter = 0
                    if player.status_effects and random.random() <= 0.05:
                        removed = random.choice(player.status_effects)
                        player.status_effects.remove(removed)
                        print(f"The nest hums softly... {player.name} feels lighter. Status effect removed: {removed}")
                else:
                    stam_gain = base_stam - rest_penalty
                    hp_gain = base_hp - rest_penalty


                # Clamp healing to non-negative
                stam_gain = max(stam_gain, 0)
                hp_gain = max(hp_gain, 0)

                before_stam = player.stamina
                before_hp = player.health

                # Apply clamped healing
                player.stamina = min(player.stamina + stam_gain, player.max_stamina)
                player.health = min(player.health + hp_gain, player.max_health)

                # Display intended healing
                print(f"{player.name} {action_word} and recovers {stam_gain} stamina and {hp_gain} HP.")

                player.clamp_stats()
                player.rest_counter += 1

                print("\n=== PLAYER STATS ===")
                print(f"Name:         {player.name}")
                print(f"Max Health:   {player.max_health}")
                print(f"Health:       {player.health}")
                print(f"Max Stamina:  {player.max_stamina}")
                print(f"Stamina:      {player.stamina}")
                print(f"Luck:         {player.luck}")
                print(f"Protection:   {player.protection}")
                print(f"Light:        {player.light}")
                print(f"Damage:       {player.damage}")
                print(f"Status:       {player.status_effects}")
                print("====================\n")

                print(f"=== PLAYER LINE ===")
                print(player.to_line())
                print("=== PLAYER LINE ===\n")

            elif choice == '3':
                if self.items:
                    self.use_item(player)
                else:
                    print("No items available!")

            elif choice == '4':
                break

            elif choice == '6':
                self.armor_menu(player)

            elif choice == '5':
                biome_input = input("What biome are you in?: ").strip().capitalize()
                full_biome = None

                for biome, abbrev in BIOME_ABBREVIATIONS.items():
                    if biome_input.upper() == abbrev or biome_input.lower() == biome.lower():
                        full_biome = biome
                        break

                if not full_biome or full_biome not in self.biomes:
                    print("Invalid biome. Returning to menu.")
                    continue

                if random.random() > 0.35:
                    print(f"{player.name} encountered no beasts.")
                    continue

                possible_creatures = [c for c in self.creature_templates if c.biome == full_biome]
                num_creatures = random.randint(1, 2)

                self.creatures = []
                predators = [c for c in possible_creatures if c.is_predator]
                for creature in random.choices(predators, k=num_creatures):
                    new_creature = Creature(
                        creature.name,
                        creature.abbreviation,
                        creature.biome,
                        creature.damage,
                        creature.health,
                        creature.drops,
                        creature.exp_range,
                        creature.is_predator,
                        creature.status_effects.copy(),
                        creature.special_ability,
                        creature.luck
                    )
                    new_creature.reset_health()
                    self.creatures.append(new_creature)

                print("\n=== CREATURE ENCOUNTER ===")
                creature_summary = {}
                for creature in self.creatures:
                    creature_summary[creature.name] = creature_summary.get(creature.name, 0) + 1
                summary = ", ".join(f"{count} {name}" for name, count in creature_summary.items())
                print(f"{player.name} encountered {summary}!")
                print("===========================\n")

                self.start_battle()

            else:
                print("Invalid option. Please try again.")

            

    def armor_menu(self, player):
        # Armor database
        ARMOR_ITEMS = {
            "AntlerHood": {"damage": 3, "protection": 3},
            "StonyHideLegwraps": {"protection": 8},
            "WovenHood": {"protection": 2},
            "WovenVest": {"protection": 4},
            "WovenLegwraps": {"protection": 3},
            "FurHood": {"protection": 3},
            "FurVest": {"protection": 6},
            "FurLegwraps": {"protection": 5},
            "HideHood": {"protection": 5},
            "HideVest": {"protection": 9},
            "HideLegwraps": {"protection": 7},
            "BoneHood": {"protection": 6},
            "BoneVest": {"protection": 11},
            "BoneLegwraps": {"protection": 8},
            "SpikedCollar": {"protection": 2, "damage": 5},
            "ShellPendant": {"luck": 10, "damage": 3},
            "ForestLuckCharm": {"luck": 10}
        }
        print("\n=== ARMOR LIST ===")
        for name, boosts in ARMOR_ITEMS.items():
            boost_str = ", ".join(f"+{v} {k.capitalize()}" for k, v in boosts.items())
            print(f"- {name}: {boost_str}")
        print("===================\n")

        action = input("Are you equipping or unequipping? ").strip().lower()
        if action not in ['equipping', 'unequipping']:
            print("Invalid action. Must be 'equipping' or 'unequipping'.")
            return

        item_name = input("What are you equipping/unequipping? ").strip().replace(" ", "")
        item = ARMOR_ITEMS.get(item_name)

        if not item:
            print(f"{item_name} not found.")
            return

        modifier = 1 if action == 'equipping' else -1

        print(f"\n{action.title()} {item_name}...")

        for stat, boost in item.items():
            if hasattr(player, stat):
                old_val = getattr(player, stat)
                setattr(player, stat, old_val + (boost * modifier))
                print(f"{'+' if modifier > 0 else '-'}{boost} {stat.capitalize()}!")

        # Display updated stats
        print("\n=== UPDATED PLAYER STATS ===")
        print(f"Name:         {player.name}")
        print(f"Max Health:   {player.max_health}")
        print(f"Health:       {player.health}")
        print(f"Max Stamina:  {player.max_stamina}")
        print(f"Stamina:      {player.stamina}")
        print(f"Luck:         {player.luck}")
        print(f"Protection:   {player.protection}")
        print(f"Light:        {player.light}")
        print(f"Damage:       {player.damage}")
        print(f"Status:       {player.status_effects}")
        print("============================\n")

        print("=== PLAYER LINE ===")
        print(player.to_line())
        print("====================")


    def use_item(self, player):
        print("\n" * 21)
        print("Choose an item to use by typing its abbreviation:")

        abbrev = input("Enter item abbreviation: ").upper()
        item = next((i for i in self.items if i.abbreviation == abbrev), None)

        if item:
            try:
                quantity = int(input(f"How many {item.name} do you want to use? "))
                if quantity <= 0:
                    print("You must use at least one.")
                    return
            except ValueError:
                print("Invalid number.")
                return

            if any(k in item.effects for k in ['heal', 'remove_status', 'stamina', 'boost_protection']):
                print("\nChoose target player:")
                for idx, pl in enumerate(self.players, 1):
                    print(f"{idx}. {pl.name} - HP: {pl.health}/{pl.max_health}")

                try:
                    target_idx = int(input("Enter player number: ")) - 1
                    if 0 <= target_idx < len(self.players):
                        target = self.players[target_idx]

                        display_header(player.name + "'s Turn")

                        raw_heal = 0
                        raw_stamina = 0
                        total_protection = 0
                        removed_status = None

                        for _ in range(quantity):
                            for effect, value in item.effects.items():
                                if effect == "heal":
                                    raw_heal += value
                                    healed = min(value, target.max_health - target.health)
                                    target.health += healed

                                elif effect == "stamina":
                                    raw_stamina += value
                                    restored = min(value, target.max_stamina - target.stamina)
                                    target.stamina += restored

                                elif effect == "boost_protection":
                                    target.temp_protection += value
                                    total_protection += value

                                elif effect == "remove_status":
                                    effect_removers = {
                                        "Wound Salve": "bleeding",
                                        "Poison Cleanser": "poison",
                                        "Catmint": "illness",
                                        "Burdock Root": "poison",
                                        "Corrupted Cleanse": "RED_BLIGHT",
                                        "Moonstone Tonic": "RED_BLIGHT",
                                    }
                                    effect_to_remove = effect_removers.get(item.name)
                                    if isinstance(target.status_effects, list):
                                        match = next((s for s in target.status_effects if s.lower() == effect_to_remove.lower()), None)
                                        if match:
                                            target.status_effects.remove(match)
                                            removed_status = effect_to_remove

                        if raw_heal:
                            print(f"{target.name} healed {raw_heal} HP total!")
                        if raw_stamina:
                            print(f"{target.name} regained {raw_stamina} stamina total!")
                        if total_protection:
                            print(f"{target.name} gained {total_protection} protection total!")
                        if removed_status:
                            print(f"{target.name} is no longer affected by {removed_status}.")

                        print(target.to_line())
                        self.items_used[item.name] = self.items_used.get(item.name, 0) + quantity
                        print(f"\n✅ Used {quantity} x {item.name} on {target.name}.\n")
                    else:
                        print("Invalid target selection.")
                except ValueError:
                    print("Please enter a valid number.")
            else:
                print("This item doesn't have healing/support effects yet handled.")
        else:
            print("Item not found.")



    def sell_items(self, item_values):
        print("=== KYMERA’S TRADING POST ===")
        response = input("Do you have the Budgeteer title? (y/n): ").lower()
        has_trader = response =='y'
        print("")
        print("Kymera peers at your items with calculating eyes...")

        item_to_sell = input("\nWhat item are you offering to trade? (type full name or 'exit'): ").strip()
        if item_to_sell.lower() == "exit":
            return

        if item_to_sell not in item_values:
            print("Kymera scoffs. 'I've no use for that.'")
            return

        try:
            quantity = int(input("How many are you offering?: "))
            if quantity <= 0:
                print("Kymera scowls. 'Nothing? Then be gone.'")
                return
        except ValueError:
            print("Kymera turns away, unimpressed by nonsense.")
            return

        base_value = item_values[item_to_sell] * quantity
        adjusted_value = base_value * 1.15 if has_trader else base_value

        pool = [i for i in item_values if abs(item_values[i] - adjusted_value) <= 5 and i != item_to_sell]
        if not pool:
            print("Kymera has nothing suitable to offer right now.")
            return

        extra_items = 1 if has_trader else 0
        offer = random.sample(pool, min(1 + quantity // 3 + extra_items, len(pool)))

        print(f"\nYou offer {quantity}x {item_to_sell}...")
        print("Kymera calculates quietly...")
        print("She offers you:")
        for i in offer:
            print(f" → {i}")

        if input("\nWill you accept her offer? (y/n): ").lower() != "y":
            print("Kymera shrugs, unimpressed by your hesitation.")
        else:
            print("Kymera nods slowly. 'A reasonable exchange.'")

    def handle_creature_defeat(self, target_creature):
        if target_creature.health <= 0:
            print("─" * 50)
            print(f"☠️ {target_creature.name} is Defeated!".center(50))
            print("─" * 50)

            target_creature.health = 0
            drops, exp_gained = target_creature.generate_drops()
            for item, quantity in drops.items():
                self.total_drops[item] = self.total_drops.get(item, 0) + quantity

            self.total_exp += exp_gained

            if target_creature in self.creatures:
                idx = self.creatures.index(target_creature)
                self.creatures.remove(target_creature)
                # Fix the index if we were pointing to this creature or anything after
                if self.current_creature_index > idx:
                    self.current_creature_index -= 1
                elif self.current_creature_index == idx:
                    # Don't increment index in main loop; we already moved
                    pass
            return True
        return False
    def distribute_drops_to_players(self):
        print("\n--- 📦 Distributing Drops To Players 📦 ---")
        for player in self.players:
            print(f"\n🎒 {player.name}'s Loot:")
            for item, total_qty in self.total_drops.items():
                give_qty = random.randint(0, min(3, total_qty))  # Up to 3 max, or 0
                if give_qty > 0:
                    print(f"    → {give_qty}x {item}")



    def start_battle(self):
        current_creature = self.creatures[self.current_creature_index]

        print(f"\n\U0001fa78\u2501\u2501\u2501[ {current_creature.name} Approaches ]\u2501\u2501\u2501\U0001fa78")
        print(f"\n \U0001f9e0 Health: {current_creature.health}")
        print(f"\n \U0001f4a5 Damage: {current_creature.damage}\n")

        self.total_drops = {}
        self.total_exp = 0

        for creature in self.creatures:
            creature.reset_health()

        battle_ended = False
        while not battle_ended:
            self.update_temp_boosts()

            if self.current_creature_index >= len(self.creatures):
                alive_creatures = [c for c in self.creatures if c.health > 0]
                if alive_creatures:
                    self.current_creature_index = self.creatures.index(alive_creatures[0])
                    active_creature = self.creatures[self.current_creature_index]
                if creature.escaped:
                    log_action(f"{active_creature.name} has already escaped and is no longer part of the fight!")
                    self.current_creature_index += 1
                    return
                else:
                    print("All creatures have been defeated!")
                    battle_ended = True
                    break

            active_creature = self.creatures[self.current_creature_index]

            while active_creature.health <= 0 or active_creature.escaped:
                if active_creature.escaped:
                    log_action(f"{active_creature.name} has already escaped and is no longer part of the fight!")
                else:
                    print(f"{active_creature.name} has fallen!")
                self.current_creature_index += 1
                if self.current_creature_index >= len(self.creatures):
                    print("All creatures have been defeated or escaped!")
                    return
                active_creature = self.creatures[self.current_creature_index]

            if active_creature.attempt_escape_creature(self):
                self.current_creature_index -= 1
                if self.current_creature_index < 0:
                    self.current_creature_index = 0
                if not self.creatures:
                    log_action("All prey creatures have escaped!")
                    return
                continue

            print("\n--- \u26a0 Current Creature \u26a0 ---")
            print(f"\nYou are facing a {active_creature.name} with {active_creature.health} HP.")
            print("\n---                        ---\n\n\n\n")
            print("\u23bb\u23bb\u23bb\u23bb\u23bb TURN OVER \u23bb\u23bb\u23bb\u23bb\u23bb")
            active_creature = self.creatures[self.current_creature_index]
            for player in self.players:
                if player.health <= 0:
                    continue

                if not self.creatures:  # all creatures gone mid-loop
                    battle_ended = True
                    break

                # Refresh active creature after any potential death
                if self.current_creature_index >= len(self.creatures):
                    self.current_creature_index = 0

                active_creature = self.creatures[self.current_creature_index]

                player.apply_status_effects()
                if player.health > 0:
                    while True:
                        print(f"\n{player.name}'s turn!")
                        action = input("Enter an action: ").strip().lower()

                        if not self.process_player_action(player, action, active_creature):
                            print("Invalid action. Try again.")
                            continue
                        break

            if active_creature.health > 0:
                alive_players = [p for p in self.players if p.health > 0]
                if alive_players:
                    if (
                        self.taunted_by
                        and self.taunt_turns_remaining > 0
                        and self.taunted_by.health > 0
                        and self.taunted_by in self.players  # ✅ Make sure they're still in battle
                    ):
                        target_player = self.taunted_by
                    else:
                        target_player = random.choice(alive_players)


                    display_header(active_creature.name + "'s Turn")
                    rage_triggered = self.determine_rage_state(active_creature)
                    if rage_triggered:
                        print(f"\n💢 {active_creature.name.upper()} ENTERS {rage_triggered.upper()} MODE! 💢")

                        if rage_triggered == "feral":
                            active_creature.damage = int(active_creature.damage * 2.5)
                            print(f"{active_creature.name} now deals MASSIVE damage!")

                        elif rage_triggered == "corrupted bloodlust":
                            print(f"{active_creature.name}'s body warps with corruption. RED_BLIGHT spreads...")

                        elif rage_triggered == "feast":
                            active_creature.damage += 2
                            print(f"{active_creature.name} enters a feast frenzy—driven by the scent of blood!")
                        if active_creature.rage_triggered:
                            active_creature.rage_turns -= 1

                            if active_creature.rage_type == "feast":
                                heal_amount = int(active_creature.max_health * 0.10)
                                active_creature.health = min(active_creature.health + heal_amount, active_creature.max_health)
                                log_action(f"{active_creature.name} tears into its own flesh—regaining {heal_amount} HP.")

                            elif active_creature.rage_type == "corrupted bloodlust":
                                if target_player and "RED_BLIGHT" not in target_player.status_effects:
                                    target_player.add_status_effect("RED_BLIGHT")
                                    log_action(f"{active_creature.name}'s corruption infects {target_player.name} with RED_BLIGHT!")
                                
                                # 💥 Add bonus damage temporarily
                                bonus_damage = 10
                                active_creature.damage += bonus_damage
                                log_action(f"{active_creature.name} lashes out in bloodlust!")

                            # End of rage
                            if active_creature.rage_turns <= 0:
                                log_action(f"{active_creature.name}'s rage fades...")
                                active_creature.rage_triggered = False
                                active_creature.rage_type = None
                                active_creature.damage = active_creature.original_damage
                    active_creature.attack(target_player)
 

            if all(creature.health <= 0 for creature in self.creatures):
                battle_ended = True
            if all(player.health <= 0 for player in self.players):
                battle_ended = True
            if self.taunt_turns_remaining > 0:
                self.taunt_turns_remaining -= 1
                if self.taunt_turns_remaining == 0:
                    self.taunted_by = None
                    log_action("The taunt effect has worn off.")

        # Only move to next creature if current one survived
        if self.current_creature_index < len(self.creatures):
            active_creature = self.creatures[self.current_creature_index]
            if active_creature.health > 0 and not active_creature.escaped:
                self.current_creature_index += 1


        if battle_ended:
            self.end_battle()

    def process_player_action(self, player, action, active_creature):
        if action == 's':
            print("\n" * 21)
            print(f"\n=== {player.name}'s Current Stats ===")
            print(f"Health: {player.health}/{player.max_health}")
            print(f"Stamina: {player.stamina}/{player.max_stamina}")
            print(f"Damage: {player.damage}")
            print(f"Protection: {player.protection}")
            print(f"Status Effects: {', '.join(player.status_effects) if player.status_effects else 'None'}")
            print(f"\n===                               ===")
            print(f"\n=== {active_creature.name}'s Stats ===")
            print(f"Health: {active_creature.health}/{active_creature.max_health}")
            print(f"Damage: {active_creature.damage}")
            print(f"\n===                               ===")
            while True:
                follow_up_action = input("Choose your action: ").strip().lower()
                if self.process_player_action(player, follow_up_action, active_creature):
                    return True
                print("Invalid action. Try again.")
                return False

        elif action == 'a':
            miss_chance = 0.15
            if player.luck < active_creature.luck:
                miss_chance += min((active_creature.luck - player.luck) * 0.08, 0.60)
            if random.random() < miss_chance:
                display_header(player.name + "'s Turn")
                print(f"\n{player.name}'s attack misses {active_creature.name}!")
                print(f"{active_creature.name} has {active_creature.health}/{active_creature.max_health} HP remaining!\n")
                return True
    
            damage = player.damage
            if random.random() <= 0.20:
                damage *= 2
                print("\n" * 21)
                print("\U0001f4a5" * 3 + " CRITICAL HIT! " + "\U0001f4a5" * 3)
    
            active_creature.health -= damage
            display_header(player.name + "'s Turn")
            print(f">> {player.name} hits for {damage} damage!")
            print(f"{active_creature.name} has {active_creature.health}/{active_creature.max_health} HP remaining!\n")
    
            if active_creature.health <= 0:
                active_creature.health = 0
                drops, exp_gained = active_creature.generate_drops()
                for item, quantity in drops.items():
                    self.total_drops[item] = self.total_drops.get(item, 0) + quantity
                self.total_exp += exp_gained

                # ✅ FIX INSERTED
                if active_creature in self.creatures:
                    idx = self.creatures.index(active_creature)
                    if active_creature.health <= 0:
                        self.handle_creature_defeat(active_creature)
                        return True

            return True

        elif action in ('gw', 'ft', 'fl', 'qn'):
            target_player = self.choose_target(for_heal=True)
            if target_player:
                getattr(player, {
                    'gw': 'groom_wounds',
                    'ft': 'field_tend',
                    'fl': 'frantic_licks',
                    'qn': 'quick_nudge'
                }[action])(target_player)
            return True

        elif action in ('hp', 'pl', 'ns', 'm', 'dcw', 'ss', 'rc'):
            target_player = self.choose_target()
            if target_player:
                getattr(player, {
                    'hp': 'heavy_pounce',
                    'pl': 'precise_lunge',
                    'ns': 'noxious_snarl',
                    'm': 'maul',
                    'dcw': 'double_claw',
                    'ss': 'shoulder_slam',
                    'rc': 'ram_charge'
                }[action])(target_player)
                if self.handle_creature_defeat(target_player):
                    return True
            return True

        elif action in ('b', 'dc', 'wh'):
            getattr(player, {
                'b': 'bristle',
                'dc': 'defensive_crouch',
                'wh': 'war_howl'
            }[action])()
            return True
        elif action == 't':
            player.taunt(self)  # ← pass battle instance
            return True

        elif action == 'sf':
            print("\n🛠️ STAT FIX TOOL 🛠️")
            print("Which stat do you want to fix?")
            print("→ h = Health")
            print("→ d = Damage")
            print("→ s = Stamina")
            print("→ l = Luck")
            print("→ p = Protection")
            stat_code = input("Enter stat code: ").strip().lower()
            valid_stats = {
                'h': 'health',
                'd': 'damage',
                's': 'stamina',
                'l': 'luck',
                'p': 'protection'
            }
            if stat_code not in valid_stats:
                print("❌ Invalid stat code.")
                return False
            try:
                new_value = int(input(f"Enter the new value for {valid_stats[stat_code]}: ").strip())
                setattr(player, valid_stats[stat_code], new_value)
                print(f"✅ {player.name}'s {valid_stats[stat_code]} set to {new_value}.")
            except ValueError:
                print("❌ Invalid number input.")
                return False
            return True

        elif action == 'e':
            if self.attempt_escape_player(player, active_creature):
                self.players.remove(player)
                if not self.players:
                    print("All players have escaped! Ending the battle.")
                    return True
            return True

        elif action == 'rn':
            self.roar_of_need(player)
            return True

        elif action == 'j':
            self.join_new_player()
            print(f"{player.name} can now take another action.")
            return True

        elif action == 'ui':
            self.use_item(player)
            return True

        return False

# Main Execution
players = []  # Start with an empty list of players
battle = Battle(players, None)  # Pass None for now

# Now that Battle exists, get its creature list
creature_templates = battle.creature_templates

# Create bounty system using that list
bounty_system = BountySystem(ITEM_VALUES, creature_templates)

# Now update battle to hold it
battle.bounty_system = bounty_system

# Start the game and prompt for actions immediately
battle.choose_action()
