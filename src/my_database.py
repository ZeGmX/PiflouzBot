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
        return self.element.keys()


    def values(self):
        """
        Implements the general dict values method
        --
        output:
            res: dict_values
        """
        return self.element.values()
    

    def items(self):
        """
        Implements the general dict items method
        --
        output:
            res: dict_items
        """
        return self.element.items()


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
        if not os.path.exists(parent_folder):
            os.mkdir(parent_folder)
        if not os.path.exists(f"{parent_folder}/{folder}"):
            os.mkdir(f"{parent_folder}/{folder}")
        
        self._save(self, f"{parent_folder}/{folder}")


    def _save(self, folder: str = None) -> None:
        if folder is None:
            folder = self.folder

        for key in self.keys():
            self._save_key(key, folder)

        
    def _load(self, folder: str = None) -> None:
        if folder is None:
            folder = self.folder

        keys = os.listdir(folder)
        for key in keys:
            self._load_key(key[:-7], folder)
    

    def _save_key(self, key: str, folder: str) -> None:
        pickle.dump(Element.convert_from_element(self[key]), open(f"{folder}/{key}.dumped", "wb"))
    

    def _load_key(self, key: str, folder: str) -> None:
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