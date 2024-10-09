import random

from constant import Constants
import events


class RandomPool:
    def __init__(self, name, pool=None):
        """
        Parameters
        ----------
        name : str
            Name of the pool (used as an identifier)
        pool : list, optional
            A list of tuples (item, weights), by default None (empty pool)
        """
        self.name = name
        self.pool = pool or []

    def to_dict(self):
        """
        Transforms the pool into a dictionary that can be saved in the database

        Returns
        -------
        dict
            Pool representation as a dictionary
        """
        return {"name": self.name, "pool": self.pool}

    @staticmethod
    def from_dict(data):
        """
        Creates a RandomPool object from a dictionary

        Parameters
        ----------
        data : dict
            RandomPool representation as a dictionary

        Returns
        -------
        RandomPool
            Corresponding RandomPool object
        """
        name = data["name"]
        pool = data["pool"]
        return RandomPool(name, pool)

    @staticmethod
    def represents_pool(val):
        """
        Checks wether the value represents a pool

        Parameters
        ----------
        val : Any
            Value to check
        """
        return isinstance(val, RandomPool) or (isinstance(val, dict) and "name" in val and "pool" in val)

    def get_random(self):
        """
        Selects a random item from the pool based on the weights of the items

        Returns
        -------
        Any
            Random item from the pool. If the item is also a pool, it will return one of its items
        """
        items = [val[0] for val in self.pool]
        weights = [val[1] for val in self.pool]

        if len(weights) == 0: return None
        item = random.choices(items, weights)[0]

        while RandomPool.represents_pool(item):
            item = RandomPool.from_dict(item).get_random()

        return item

    def update(self, other_pool):
        """
        Returns an updated pool with the items from another pool

        Parameters
        ----------
        other_pool : dict
            The pool to update with

        Returns
        -------
        RandomPool
            Updated pool
        """
        new_pool = []

        for item, weight in self.pool:
            for other_item, other_weight in other_pool.pool:
                if RandomPool.represents_pool(item) and RandomPool.represents_pool(other_item):
                    if item["name"] == other_item["name"]:
                        new_pool.append(RandomPool.from_dict(item).update(RandomPool.from_dict(other_item)), other_weight)
                if item == other_item:
                    new_pool.append((item, other_weight))
            if item not in [val[0] for val in new_pool]:
                new_pool.append((item, weight))

        for other_item, other_weight in other_pool.pool:
            if other_item not in [val[0] for val in new_pool]:
                new_pool.append((other_item, other_weight))

        return RandomPool(self.name, new_pool)


class RandomPoolTable:
    def __init__(self, pools=None):
        self.pools = pools or []

    def to_dict(self):
        """
        Transforms the pool table into a dictionary that can be saved in the database

        Returns
        -------
        dict
            Pool table representation as a dictionary
        """
        return {"pools": [(pool.to_dict(), proba) for pool, proba in self.pools]}

    def update(self, other_table):
        """
        Updates the pool table with the pools from another table and returns the new table

        Parameters
        ----------
        other_table : RandomPoolTable
            The table to update with

        Returns
        -------
        RandomPoolTable
            Updated table
        """
        new_pools = []
        names = []
        for old_pool, old_proba in self.pools:
            for other_pool, other_proba in other_table.pools:
                if old_pool.name == other_pool.name:
                    new_pool = old_pool.update(other_pool)
                    new_pools.append((new_pool, other_proba))
                    names.append(old_pool.name)
                    break
            if len(names) == 0 or old_pool.name != names[-1]:  # If the pool was not updated
                new_pools.append((old_pool, old_proba))

        for other_pool, other_proba in other_table.pools:
            if other_pool.name not in names:
                new_pools.append((other_pool, other_proba))

        return RandomPoolTable(new_pools)

    @staticmethod
    def from_dict(data):
        """
        Creates a RandomPoolTable object from a dictionary

        Parameters
        ----------
        data : dict
            RandomPoolTable representation as a dictionary

        Returns
        -------
        RandomPoolTable
            Corresponding RandomPoolTable object
        """
        pools = [(RandomPool.from_dict(pool), proba) for pool, proba in data["pools"]]
        return RandomPoolTable(pools)

    @staticmethod
    def compute_pibox_table():
        """
        Returns a RandomPoolTable object for the pibox drop table

        Returns
        -------
        RandomPoolTable
            Pibox drop table
        """
        default = Constants.PIBOX_POOL_TABLE

        event = events.get_event_object(events.EventType.PASSIVE)
        if event is not None:
            event_table = event.get_pibox_pool_table()
            return default.update(event_table)
        return default
