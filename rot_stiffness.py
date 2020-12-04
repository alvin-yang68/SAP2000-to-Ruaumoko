# -*- coding: utf-8 -*-
"""
Created on Fri Apr 12 09:31:28 2019

@author: alvin
"""

from converter import get_s2k_data
from config import data_retriever
import config as cfg

class PartialFixity:
    def __init__(self, frame_id, length, I33, I22):
        self.frame_id = frame_id
        self.length = length
        self.I33 = I33
        self.I22 = I22
        self.k_rot_33 = self._get_k_rot(self.I33, self.length)
        self.k_rot_22 = self._get_k_rot(self.I22, self.length)
        self.M3I = ''
        self.M2I = ''
        self.M3J = ''
        self.M2J = ''
        
    def _get_k_rot(self, I, L):
        return str(round((cfg.alpha_rot_stiff * cfg.E_rot_stiff * I) / L))
    
    def set_fixity(self, release_def):
        if release_def[cfg.M3I] == cfg.yes_rel:
            self.M3I = self.k_rot_33
        if release_def[cfg.M2I] == cfg.yes_rel:
            self.M2I = self.k_rot_22
        if release_def[cfg.M3J] == cfg.yes_rel:
            self.M3J = self.k_rot_33
        if release_def[cfg.M2J] == cfg.yes_rel:
            self.M2J = self.k_rot_22
    
    def get_partial_fixity(self):
        txt_form = '{0}\t\t\t\t\t{1}\t{2}\t\t\t\t\t{3}\t{4}'.format(
                self.frame_id, self.M2I, self.M3I, self.M2J, self.M3J)
        
        return txt_form

s2k_file_path = 'Apartment Building Model - 25d.s2k'

# Get the raw s2k file (s2k_raw) and its associated table of contents
with open(s2k_file_path, 'r') as s2k_file:
    s2k_data = get_s2k_data(s2k_file)

# Frame ID -> Length
s2k_frm_conn = data_retriever(s2k_data, cfg.title_frame_conn)
get_frm_len =  {line[cfg.frame_conn] : line[cfg.length] for line in s2k_frm_conn}

# Section name -> I33
s2k_sec_def = data_retriever(s2k_data, cfg.title_frame_sec_def)
get_sec_I33 = {}
get_sec_I22 = {}
for line in s2k_sec_def:
    get_sec_I33.update({line[cfg.sec_name] : line[cfg.sec_Izz]})
    get_sec_I22.update({line[cfg.sec_name] : line[cfg.sec_Iyy]})

# Frame ID -> section name
s2k_sec_ass = data_retriever(s2k_data, cfg.title_frame_sec_ass)
get_sec_name = {line[cfg.frame_sec] : line[cfg.sect_name] for line in s2k_sec_ass}

# All frame IDs with releases
s2k_frm_rel = data_retriever(s2k_data, cfg.title_frame_release)

partial_fixity = []

for line in s2k_frm_rel:
    frame_id = line[cfg.frame_rel]
    frame_length = float(get_frm_len[frame_id])
    section_name = get_sec_name[frame_id]
    I33 = float(get_sec_I33[section_name])
    I22 = float(get_sec_I22[section_name])
    
    frame_release = PartialFixity(frame_id, frame_length, I33, I22)
    frame_release.set_fixity(line)
    partial_fixity.append(frame_release.get_partial_fixity())

txt_form = '\n'.join(partial_fixity)

with open('partial_fixity.txt', 'w') as file:
    file.write(txt_form)