# TODO: fix mutating the databse using .items() or through iteration

import pickle
import os


    
# Mutable elements in the database
# In the database, they are stored as the actual element (list, dict), but when accessed, they are converted to Element_list or Element_dict
class Element:
    """
    Class for mutable elements in the database
    """

    element = None
    db_key = ""

    def __init__(self, db_key, element):
        self.db_key = db_key
        self.element = element


    @staticmethod
    def convert_to_element(item, db_key):
        """
        Converts a general database item to an Element_list or Element_dict
        No effect if the item is not a list or a dict
        --
        input:
            item: any
            db_key: str
        """
        if type(item) == list:
            return Element_list(db_key, item)
        elif type(item) == dict:
            return Element_dict(db_key, item)
        else:
            return item
        
    @staticmethod
    def convert_from_element(item):
        """
        Converts an Element_list or Element_dict to a general database item
        No effect if the item is not an Element_list or Element_dict
        --
        input:
            item: any
        """
        if type(item) == Element_list:
            return list(Element.convert_from_element(item) for item in item.element)
        elif type(item) == Element_dict:
            return dict((key, Element.convert_from_element(value)) for key, value in item.element.items())
        else:
            return item
    

    def get_element(self):
        """
        Returns the initial database item
        --
        output:
            item: list or dict
        """
        return self.element
    

    def __setitem__(self, key, value):
        assert db._check_if_acceptable(value), "Value could not be appended because it contains an unacceptable type"
        self.element[key] = value
        db._save_key(self.db_key, db.folder)


    def __delitem__(self, key) -> None:
        del self.element[key]
        db._save_key(self.db_key, db.folder)
    

    def __getitem__(self, key):
        return Element.convert_to_element(self.element[key], self.db_key)


    def __str__(self) -> str:
        return str(self.element)
    

    def __repr__(self) -> str:
        return str(self.element)
    

    def __len__(self) -> int:
        return len(self.element)
    

    def __iter__(self):
        return iter(self.element)


    def __contains__(self, item) -> bool:
        return item in self.element


class Element_list(Element):
    """
    Class for mutable lists in the database
    """

    def __init__(self, db_key, element):
        assert type(element) == list
        super().__init__(db_key, element)


    def __add__(self, other):
        """
        Implements the general list add method
        --
        input:
            other: list
        """
        return self.element + other
    
    
    def append(self, item):
        """
        Implements the general list append method
        --
        input:
            item: any
        """
        assert db._check_if_acceptable(item), "Value could not be appended because it contains an unacceptable type"
        self.element.append(Element.convert_from_element(item))
        db._save_key(self.db_key, db.folder)


class Element_dict(Element):
    """
    Class for mutable dictionaries in the database
    """

    def __init__(self, db_key, element):
        assert type(element) == dict
        super().__init__(db_key, element)
    

    def keys(self):
        """
        Implements the general dict keys method
        --
        output:
            res: dict_keys
        """
        return Element_dict_keys(self.element.keys(), self.db_key)


    def values(self):
        """
        Implements the general dict values method
        --
        output:
            res: dict_values
        """
        return Element_dict_values(self.element.values(), self.db_key)
    

    def items(self):
        """
        Implements the general dict items method
        --
        output:
            res: dict_items
        """
        return Element_dict_items(self.element.items(), self.db_key)


class Element_dict_iterator:
    """
    Class for the iterators generated from .keys(), .values() and .items() methods of Element_dict
    """

    def __init__(self, collection, db_key):
        self.collection = collection
        self.db_key = db_key
        self.iterator = None
    

    def __iter__(self):
        self.iterator = iter(self.collection)
        return self


    def __next__(self):
        return Element.convert_to_element(next(self.iterator), self.db_key)
    

    def __contains__(self, item):
        return item in self.collection


    def __str__(self) -> str:
        return str(self.collection)


    def __repr__(self):
        return str(self.collection)


class Element_dict_keys(Element_dict_iterator):
    pass


class Element_dict_values(Element_dict_iterator):
    pass


class Element_dict_items(Element_dict_iterator):
    def __next__(self):
        key, value = next(self.iterator)
        return (Element.convert_to_element(key, self.db_key), Element.convert_to_element(value, self.db_key))


class My_database(dict):
    """
    Dictionary-based database with automatic saving and loading
    """

    ACCEPTABLE_TYPES_DEFAULT = [int, float, str, bool, type(None)]
    ACCEPTABLE_TYPES_COLLECTION = [list, dict, Element_list, Element_dict]

    folder = None  # folder where the database is stored


    def __init__(self, folder: str = None) -> None:
        self.folder = folder
        
        if folder is not None:
            self._load(folder)


    ### Item handling ###

    def _check_if_acceptable(self, value):
        """
        Verifies if a value has a type acceptable for the database
        --
        input:
            value: any
        --
        output:
            res: bool
        """
        if type(value) in self.ACCEPTABLE_TYPES_DEFAULT:
            return True
        
        if type(value) in self.ACCEPTABLE_TYPES_COLLECTION:
            return all(self._check_if_acceptable(item) for item in value)
        
        return False
    

    def __getitem__(self, key):
        return Element.convert_to_element(super().__getitem__(key), key)


    # set an item
    def __setitem__(self, key, value):
        assert self._check_if_acceptable(value), "Value could not be appended because it contains an unacceptable type"
        super().__setitem__(key, Element.convert_from_element(value))
        self._save_key(key, self.folder)


    # delete an item
    def __delitem__(self, key):
        super().__delitem__(key)
        os.remove(f"{self.folder}/{key}.dumped")
    

    ### I/O ###

    def make_backup(self, parent_folder: str = "backups", folder: str = "database") -> None:
        """
        Creates a backup of the database in the specified folder
        --
        input:
            parent_folder: str -> the parent folder where the backup will be stored
            folder: str -> the name of the folder where the backup will be stored
        """
        if not os.path.exists(parent_folder):
            os.mkdir(parent_folder)
        if not os.path.exists(f"{parent_folder}/{folder}"):
            os.mkdir(f"{parent_folder}/{folder}")
        
        self._save(self, f"{parent_folder}/{folder}")


    def _save(self, folder: str = None) -> None:
        """
        Saves the database in the specified folder
        --
        input:
            folder: str -> the folder where the database will be stored
        """

        if folder is None:
            folder = self.folder

        for key in self.keys():
            self._save_key(key, folder)

        
    def _load(self, folder: str = None) -> None:
        """
        Loads the database from the specified folder
        --
        input:
            folder: str -> the folder where the database will be loaded from
        """
        if folder is None:
            folder = self.folder

        keys = os.listdir(folder)
        for key in keys:
            self._load_key(key[:-7], folder)
    

    def _save_key(self, key: str, folder: str) -> None:
        """
        Saves a key in the specified folder
        --
        input:
            key: str -> the key to be saved
            folder: str -> the folder where the key will be saved
        """
        pickle.dump(Element.convert_from_element(self[key]), open(f"{folder}/{key}.dumped", "wb"))
    

    def _load_key(self, key: str, folder: str) -> None:
        """
        Loads a key from the specified folder
        --
        input:
            key: str -> the key to be loaded
            folder: str -> the folder where the key will be loaded from
        """
        self[key] = pickle.load(open(f"{folder}/{key}.dumped", "rb"))


    


    


# db = My_database()
# db.folder = "D:/pibot/my_db"
# db._load("my_db")

db = My_database(folder="my_db")

# for key in list(db.keys()):
#     del db[key]

# a = pickle.load(open("D:/Downloads/pibot/2023_11_02_22_00_00.dump", "rb"))
# for key in list(a.keys()):
#     db[key] = a[key]