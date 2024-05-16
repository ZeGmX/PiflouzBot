import os
import pickle
from shutil import rmtree


# Mutable elements in the database
# In the database, they are stored as the actual element (list, dict), but when accessed, they are converted to Element_list or Element_dict
class Element:
    """
    Class for mutable elements in the database
    """

    element = None

    parent_dict = None  # parent information to optimize data saving on changes
    parent_key = ""

    stop_parent_propagation = False  # If a dict is in a list, we have to save the whole list, not a specific dict key, so we don't propagate the parent

    def __init__(self, parent, parent_key, element, stop_parent_propagation=False):
        self.parent_dict = parent
        self.parent_key = parent_key
        self.element = element
        self.stop_parent_propagation = stop_parent_propagation
        

    @staticmethod
    def convert_to_element(item, parent_dict, parent_key, stop_parent_propagation=False):
        """
        Converts a general database item to an Element_list or Element_dict
        No effect if the item is not a list or a dict
        --
        input:
            item: any
            parent_dict: Element_dict
            parent_key: str
        """
        if type(item) == list:
            return Element_list(parent_dict, parent_key, item)
        elif type(item) == dict:
            return Element_dict(parent_dict, parent_key, item, stop_parent_propagation)
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
        assert db._check_if_acceptable(value), "Value could not be set because it contains an unacceptable type"
        assert db._check_if_acceptable(key), "Key could not be set because it contains an unacceptable type"
        self.element[key] = Element.convert_from_element(value)

        if self.parent_dict is not None:
            self.parent_dict.save_key(self.parent_key, db.folder) 
        else: # if the element is the root of the database, it's necessarily a dict
            self.save_key(self.parent_key, db.folder) 


    def __delitem__(self, key) -> None:
        del self.element[key]

        if self.parent_dict is not None:
            self.parent_dict.save_key(self.parent_key, db.folder)
        else: # if the element is the root of the database, it's necessarily a dict
            self.save_key(self.parent_key, db.folder)
    

    def __getitem__(self, key):
        return Element.convert_to_element(self.element[key], self.parent_dict, self.parent_key, self.stop_parent_propagation)


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


    def get_folder_path(self, root_folder):
        """
        Returns the path to the subfolder where the element is stored
        --
        input:
            root_folder: str -> the folder where the whole database is stored
        --
        output:
            res: str
        """
        if self.parent_dict is None:
            return root_folder

        return self.parent_dict.get_folder_path(root_folder) + f"/{self.parent_key}"


class Element_list(Element):
    """
    Class for mutable lists in the database
    """

    def __init__(self, parent_dict, parent_key, element):
        assert type(element) == list
        super().__init__(parent_dict, parent_key, element, stop_parent_propagation=True)


    def __add__(self, other):
        """
        Implements the general list add method
        --
        input:
            other: list
        --
        output:
            res: Element_list
        """
        return Element_list(self.parent_dict, self.parent_key, self.element + other)
    
    
    def append(self, item):
        """
        Implements the general list append method
        --
        input:
            item: any
        """
        assert db._check_if_acceptable(item), "Value could not be appended because it contains an unacceptable type"
        self.element.append(Element.convert_from_element(item))
        
        self.parent_dict.save_key(self.parent_key, db.folder)


class Element_dict(Element):
    """
    Class for mutable dictionaries in the database
    """

    def __init__(self, parent_dict, parent_key, element, stop_parent_propagation=False):
        assert isinstance(element, dict)
        super().__init__(parent_dict, parent_key, element, stop_parent_propagation)
    

    def keys(self):
        """
        Implements the general dict keys method
        --
        output:
            res: dict_keys
        """
        return Element_dict_keys(self.element.keys(), self.parent_dict, self.parent_key, self.stop_parent_propagation)


    def values(self):
        """
        Implements the general dict values method
        --
        output:
            res: dict_values
        """
        if self.stop_parent_propagation:
            return Element_dict_values(self.element.values(), self.parent_dict, self.parent_key, self.stop_parent_propagation)
        return Element_dict_values(self.element.values(), self, self.parent_key, self.stop_parent_propagation) # parent_key will be set for each item
    

    def items(self):
        """
        Implements the general dict items method
        --
        output:
            res: dict_items
        """
        # items need both the dict and parent dict
        # but if the parent dict is None, we can't get the normal dict from it
        # so we pass the normal dict itself, and access the parent with the `parent_dict` attribute if needed
        return Element_dict_items(self.element.items(), self, self.parent_key, self.stop_parent_propagation) 


    def __setitem__(self, key, value):
        assert db._check_if_acceptable(value), "Value could not be set because it contains an unacceptable type"
        assert db._check_if_acceptable(key), "Key could not be set because it contains an unacceptable type"
        self.element[key] = Element.convert_from_element(value)
        if self.stop_parent_propagation:
            self.parent_dict.save_key(self.parent_key, db.folder)
        else:
            self.save_key(key, db.folder) 


    def __delitem__(self, key) -> None:
        del self.element[key]

        if self.stop_parent_propagation:  # if the dict is in a list, the key is not saved as it's own file
            self.parent_dict.save_key(self.parent_key, db.folder)
        else:
            path = f"{self.get_folder_path(db.folder)}/{key}"
            if os.path.exists(path) and os.path.isdir(path):
                rmtree(path)
            elif os.path.exists(path + ".dumped"):
                os.remove(path + ".dumped")

            
    def __getitem__(self, key):
        if self.stop_parent_propagation:
            return Element.convert_to_element(self.element[key], self.parent_dict, self.parent_key, self.stop_parent_propagation)
        return Element.convert_to_element(self.element[key], self, key, self.stop_parent_propagation)
    

    def save(self, root_folder):
        """
        Saves the dictionary in the specified folder
        If an item is also a dictionary, it will recursively be saved in a subfolder
        -- 
        input:
            root_folder: str -> the folder where the dictionary will be saved
        """
        if not os.path.exists(root_folder):
            os.mkdir(root_folder)

        if len(self.element) == 0:
            subfolder = self.get_folder_path(root_folder)
            if not os.path.exists(subfolder):
                os.mkdir(subfolder)
            return

        for key in self.keys():
            self.save_key(key, root_folder)
    

    def save_key(self, key, root_folder):
        """
        Saves the value associated with a key in the specified folder
        -- 
        input:
            key: str 
            root_folder: str
        """
        if not db.is_loaded:
            return

        value = self[key]
        subfolder = self.get_folder_path(root_folder)

        if not os.path.exists(subfolder):
            os.mkdir(subfolder)
        
        # Deletes everything in the subfolder if it's a dict
        # This allows the removal of items if e.g. db["a"] = dict() is called, where "a" was previously a dict
        if os.path.isdir(f"{subfolder}/{key}"):
            rmtree(f"{subfolder}/{key}")
        
        if isinstance(value, Element_dict):
            value.save(root_folder)
        else:
            pickle.dump(Element.convert_from_element(value), open(f"{subfolder}/{key}.dumped", "wb"))
    

    def load(self, folder):
        """
        Loads the dictionary from the specified folder
        --
        input:
            folder: str -> the folder where the dictionary will be loaded from
        """
        keys = os.listdir(folder)

        if len(keys) == 0:
            return

        for key in keys:
            if os.path.isdir(f"{folder}/{key}"):
                d = Element_dict(self, key, {})
                d.load(f"{folder}/{key}")
                self[key] = Element.convert_from_element(d)
            else:
                self[key[:-7]] = pickle.load(open(f"{folder}/{key}", "rb"))
    

    def __str__(self):
        if len(self.element) == 0:
            return "{}"
        
        res = "{\n"
        for key, value in self.items():
            val_str = value.__str__().split("\n")
            for i in range(1, len(val_str)):
                val_str[i] = "|  " + val_str[i]

            res += f"|  {key}: {"\n".join(val_str)},\n"
        return res + "}"


class Element_dict_iterator:
    """
    Class for the iterators generated from .keys(), .values() and .items() methods of Element_dict
    """

    def __init__(self, collection, parent_dict, parent_key, stop_parent_propagation=False):
        self.collection = collection
        self.parent_dict = parent_dict
        self.parent_key = parent_key
        self.iterator = None
        self.stop_parent_propagation = stop_parent_propagation
    

    def __iter__(self):
        self.iterator = iter(self.collection)
        return self


    def __next__(self):
        return Element.convert_to_element(next(self.iterator), self.parent_dict, self.parent_key, self.stop_parent_propagation)
    

    def __contains__(self, item):
        return item in self.collection


    def __str__(self) -> str:
        return str(self.collection)


    def __repr__(self):
        return str(self.collection)


class Element_dict_keys(Element_dict_iterator):
    pass


class Element_dict_values(Element_dict_iterator):
    def __iter__(self):
        self.iterator = iter(self.collection)
        self.iterator_keys = iter(self.parent_dict.element.keys())
        return self


    def __next__(self):
        key, value = next(self.iterator_keys),  next(self.iterator)
        
        if self.stop_parent_propagation:
            return Element.convert_to_element(value, self.parent_dict, self.parent_key, self.stop_parent_propagation)
        return Element.convert_to_element(value, self.parent_dict, key, self.stop_parent_propagation)


class Element_dict_items(Element_dict_iterator):
    def __next__(self):
        key, value = next(self.iterator)
        # Here, `parent_dict` is actually the child dict, so the actual parent is `parent_dict.parent_dict`
        if self.stop_parent_propagation:
            return (Element.convert_to_element(key, self.parent_dict.parent_dict, self.parent_key, self.stop_parent_propagation), Element.convert_to_element(value, self.parent_dict.parent_dict, self.parent_key, self.stop_parent_propagation))
        return (Element.convert_to_element(key, self.parent_dict.parent_dict, self.parent_key, self.stop_parent_propagation), Element.convert_to_element(value, self.parent_dict, key, self.stop_parent_propagation))


class My_database(dict):
    """
    Dictionary-based database with automatic saving and loading
    """

    ACCEPTABLE_TYPES_DEFAULT = [int, float, str, bool, type(None)]
    ACCEPTABLE_TYPES_COLLECTION = [list, dict, Element_list, Element_dict]

    folder = None  # folder where the database is stored

    is_loaded = False # prevents the database from writing before it is fully loaded


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
        return Element.convert_to_element(super().__getitem__(key), self.to_element(), key, stop_parent_propagation=False)


    # set an item
    def __setitem__(self, key, value):
        assert self._check_if_acceptable(value), "Value could not be set because it contains an unacceptable type"
        assert self._check_if_acceptable(key), "Key could not be set because it contains an unacceptable type"
        super().__setitem__(key, Element.convert_from_element(value))
        if self.is_loaded:
            self.to_element().save_key(key, self.folder)


    # delete an item
    def __delitem__(self, key):
        super().__delitem__(key)

        if os.path.exists(f"{self.folder}/{key}.dumped"):
            os.remove(f"{self.folder}/{key}.dumped")
        elif os.path.exists(f"{self.folder}/{key}"):
            rmtree(f"{self.folder}/{key}")
        else:
            print("something went wrong")
    

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
        
        self._save(f"{parent_folder}/{folder}")


    def _save(self, folder: str = None) -> None:
        """
        Saves the database in the specified folder
        --
        input:
            folder: str -> the folder where the database will be stored
        """

        if folder is None:
            folder = self.folder

        self.to_element().save(folder)
    
    
    def _load(self, folder: str = None) -> None:
        """
        Loads the database from the specified folder
        --
        input:
            folder: str -> the folder where the database will be loaded from
        """
        if folder is None:
            folder = self.folder

        d = self.to_element()
        d.load(folder)

        for key, val in d.items():
            self[key] = val

        self.is_loaded = True
    
    
    def to_element(self):
        return Element_dict(None, "", self)


    def __str__(self) -> str:
        return self.to_element().__str__()


db = My_database()
db.folder = "my_db"
db._load()