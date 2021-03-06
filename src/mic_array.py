from typing import Union
from typing import Optional
import numpy as np
import json
from exceptions import *

class Mic:
    """
    Represents a single microphone in the microphone array
    """
    required_params = ["fS", "pos"]

    def __init__(self, json_mic_obj: dict, default_name: Optional[Union[int, str]] = None) -> None:
        """
        Takes a json-represented mic object and generates a Mic object

        Arguments:
        json_mic_obj -- a dictionary that comes from parsing a json object representing a single microphone
        """

        for param in Mic.required_params:
            if param not in json_mic_obj:
                raise ConfigError(f"Mic config json missing required parameter {param}, attempted to parse json object:\n {json.dumps(json_mic_obj, indent=4)}")
        
        self.name : str        = json_mic_obj["name"] if "name" in json_mic_obj else default_name
        self.fS   : int        = json_mic_obj["fS"]
        self.pos  : np.ndarray = np.array(json_mic_obj["pos"])

class MicArray:
    """
    Form a microphone array object from json specification.

    Attributes:
    nChannels   -- the number of microphones/channels in the array (assumed each mic is 1 channel)
    mics        -- an array of microphone objects corresponding to microphones in the array
    name_to_mic -- dictionary from microphone name to microphone object
    """

    def __init__(self, cfg_fname: str) -> None:
        """
        Takes and loads json microphone configuration file that specifies microphone array.

        Arguments:
        cfg_fname -- a config filename specifying the microphone array. See mic_cfg.json for an example.
        """
        self.cfg_fname = cfg_fname
        self._load_cfg()

        # None if validate_names has not been called, else True if names are valid, False if not.
        self.valid_names = None

        self.name_to_mic: dict[str, Mic] = {mic.name: mic for mic in self.mics}


    def _load_cfg(self) -> None:
        
        with open(self.cfg_fname) as f:
            data = json.load(f)
        
        self.nChannels = len(data) # i.e. number of microphones

        self.mics: list[Mic] = []

        for json_mic_obj in data:
            self.mics.append(Mic(json_mic_obj))
    
    def validate_names(self) -> bool:
        """
        Returns true if each mic has a valid name, false if not. Checks to ensure names are unique. Does not check for this, but all names must be a string or int (all names must have the same type).

        Call this method if you need each microphone to have a valid name. Otherwise, mics can be accessed by index.
        """

        names = set()

        for mic in self.mics:
            if mic.name is None or mic.name in names:
                self.valid_names = False
                return self.valid_names
            names.add(mic.name)
        
        self.valid_names = True
        return self.valid_names
    
    def gen_names(self) -> None:
        """
        Generates names for each microphone (each mic has an integer name, 0, 1, etc.)
        """
        
        for idx, mic in enumerate(self.mics):
            mic.name = idx
    
    def get_sample_freq(self) -> Union[int, None]:
        """
        Returns the sample frequency of the mic array if all mics sample at the same frequency, else None
        """
        rval = None
        for mic in self.mics:
            if rval is not None and rval != mic.fS:
                return None
            rval = mic.fS
        return rval
            
    def __contains__(self, name: str) -> bool:
        """
        Checks to see if the mic array contains a mic with name given by name
        """

        return name in self.name_to_mic

    def set_mic_locs(self, locs: dict[Union[int, str], Union[list[float], np.ndarray]]) -> None:
        """
        Takes a dictionary from mic name to 3D coordinate position and updates the locations of the mics given in the dictionary
        """
        for mic_name, pos in locs.items():
            if mic_name in self:
                self.name_to_mic[mic_name].pos = np.array(pos)
            else:
                raise InvalidInput(f"Mic name {mic_name} does not exist in the mic array")
    
    
