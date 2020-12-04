# -*- coding: utf-8 -*-
"""
props.py: The s2k sections to rmk props convert module, which  defines the 
functions required to perform conversion, as well as other utilities.
"""

import config as cfg
from config import data_retriever

def convert(s2k_data):
    """
    Converts the s2k frame and joint link sections to rmk member properties. 
    This is the main function of this module which executes the other functions.
    """
    raw_strct_mmbr_props = {}       # {section label : rmk_mmbr_props}
    
    # Update the raw_strct_mmbr_props for gravity columns
    raw_strct_mmbr_props = get_grav_col_props(raw_strct_mmbr_props)
    
    # Update the raw_strct_mmbr_props for frame (beam/column) elements
    raw_strct_mmbr_props, get_rmk_frm_props = get_frm_mmbr_props(
            s2k_data, raw_strct_mmbr_props)
    
    # Update the raw_strct_mmbr_props for link elements
    raw_strct_mmbr_props, get_rmk_link_props = get_link_mmbr_props(
            s2k_data, raw_strct_mmbr_props)
    
    rmk_mmbr_props_txt = txt_format(raw_strct_mmbr_props)
    get_rmk_props_no = {'frame' : get_rmk_frm_props, 'link' : get_rmk_link_props}
    
    return rmk_mmbr_props_txt, get_rmk_props_no

def get_grav_col_props(raw_strct_mmbr_props):
    """ Set the member properties for a gravity column. """
    rmk_line_1 = {'N':1, 'MYTYPE':'FRAME', 'LABEL':'"Gravity Column"'}
    rmk_line_2 = {'ITYPE':1, 'IPINZ':3, 'IPINY':3, 'ICOND':0, 'IHYST':0, 
                  'ILOS':0, 'IDAMG':0, 'IGA':0, 'IDUCT':0}
    rmk_line_3 = {'E':0, 'G':0, 'A':0, 'Jxx':0, 'Izz':0, 'Iyy':0, 'Asz':0, 
                  'Asy':0, 'Sy':0, 'Sz':0, 'WGT':0}
    rmk_line_4 = {'END1z':0, 'END2z':0, 'END1y':0, 'END2y':0, 'FJ1z':0, 
                  'FJ2z':0, 'FJ1y':0, 'FJ2y':0, 'Y0':0, 'Z0':0}
    
    raw_strct_mmbr_props.update({rmk_line_1['LABEL'] : [rmk_line_1, rmk_line_2, 
                                 rmk_line_3, rmk_line_4]})
    
    return raw_strct_mmbr_props

def get_frm_mmbr_props(s2k_data, raw_strct_mmbr_props):
    """ Converts the s2k frame sections to rmk member properties. """  
    get_rmk_frm_props = {}      # {s2k frame no. : rmk props no.}
    
    # Organize the material mechanical properties
    s2k_mat_mech = data_retriever(s2k_data, cfg.title_mat_mech)
    get_mat_mech = {line[cfg.material] : {'E':line[cfg.E], 'G':line[cfg.G]} for 
                    line in s2k_mat_mech if {cfg.E, cfg.G}.issubset(line.keys())}
    
    # Organize the frame section definition for use later
    s2k_sec_def = data_retriever(s2k_data, cfg.title_frame_sec_def)
    get_sec_def_data = {line[cfg.sec_name] : line for line in s2k_sec_def}
    
    # Organize the frame section assignment for use later
    s2k_sec_ass = data_retriever(s2k_data, cfg.title_frame_sec_ass)
    
    # Organize the frame release assignment for use later
    s2k_frm_rel = data_retriever(s2k_data, cfg.title_frame_release)
    get_frm_rel = {line[cfg.frame_rel] : line for line in s2k_frm_rel}
    
    # Organize the frame partial fixity assignment for use later
    s2k_part_fix = data_retriever(s2k_data, cfg.title_partial_fix)
    get_part_fix = {line[cfg.frame_rel] : line for line in s2k_part_fix}
    
    # Organize the frame offset assignment for use later
    s2k_frm_off = data_retriever(s2k_data, cfg.title_frame_offset)
    get_frm_off = {line[cfg.frame_off] : line for line in s2k_frm_off 
                   if {cfg.off_y, cfg.off_z}.issubset(line.keys())}
    
    for line in s2k_sec_ass:
        frm_no = line[cfg.frame_sec]
        prop_no = len(raw_strct_mmbr_props) + 1
        sec_id = line[cfg.sect_name].strip('"')
        
        sec_def_data = get_sec_def_data[line[cfg.sect_name]]
        mat_id = sec_def_data[cfg.sec_material]
        
        rmk_line_1 = {'N':prop_no, 'MYTYPE':'FRAME', 'LABEL':'"{}'.format(sec_id)}
        rmk_line_2 = {'ITYPE':1, 'IPINZ':0, 'IPINY':0, 'ICOND':0, 'IHYST':0, 
                      'ILOS':0, 'IDAMG':0, 'IGA':0, 'IDUCT':0}
        rmk_line_3 = {'E':get_mat_mech[mat_id]['E'],
                      'G':get_mat_mech[mat_id]['G'],
                      'A':sec_def_data[cfg.sec_area],
                      'Jxx':sec_def_data[cfg.sec_Jxx],
                      'Izz':sec_def_data[cfg.sec_Izz],
                      'Iyy':sec_def_data[cfg.sec_Iyy],
                      'Asz':sec_def_data[cfg.sec_Asz],
                      'Asy':sec_def_data[cfg.sec_Asy],
                      'Sy':0, 'Sz':0, 'WGT':0}
        rmk_line_4 = {'END1z':0, 'END2z':0, 'END1y':0, 'END2y':0, 'FJ1z':0, 
                      'FJ2z':0, 'FJ1y':0, 'FJ2y':0, 'Y0':0, 'Z0':0}
        
        if frm_no in get_part_fix.keys():
            part_fix_line = get_part_fix[frm_no]
            rmk_line_4, add_sec_id = process_part_fix(part_fix_line, 
                                                      rmk_line_4)
            rmk_line_1['LABEL'] += add_sec_id
        elif frm_no in get_frm_rel.keys():
            frm_rel_line = get_frm_rel[frm_no]
            rmk_line_2, add_sec_id = process_frm_release(frm_rel_line, 
                                                         rmk_line_2)
            rmk_line_1['LABEL'] += add_sec_id
            
        if frm_no in get_frm_off.keys():
            frm_off_line = get_frm_off[frm_no]
            
            rmk_line_4, add_sec_id = process_frm_offset(frm_off_line, 
                                                        rmk_line_4)
            rmk_line_1['LABEL'] += add_sec_id
            
        rmk_line_1['LABEL'] += '"'
        
        if rmk_line_1['LABEL'] not in raw_strct_mmbr_props.keys():
            raw_strct_mmbr_props.update({rmk_line_1['LABEL'] : [rmk_line_1, 
                                         rmk_line_2, rmk_line_3, rmk_line_4]})
        else:
            prop_no = raw_strct_mmbr_props[rmk_line_1['LABEL']][0]['N']
        
        get_rmk_frm_props.update({frm_no : prop_no})
        
    return raw_strct_mmbr_props, get_rmk_frm_props

def get_link_mmbr_props(s2k_data, raw_strct_mmbr_props):
    """ Converts the s2k 1-joint link sections to rmk member properties. """  
    get_rmk_link_props = {}    # {s2k link_1 no. : rmk props no.}
    
    # Organize the link section assignment for use later
    s2k_sec_ass = data_retriever(s2k_data, cfg.title_link_prop)
    
    for line in s2k_sec_ass:
        link_no = line[cfg.link]
        prop_no = len(raw_strct_mmbr_props) + 1
        sec_id = line[cfg.prop_link].strip('"')
        
        rmk_line_1 = {'N':prop_no, 'MYTYPE':'SPRING', 'LABEL':'"{}"'.format(sec_id)}
        rmk_line_2 = {'ITYPE':1, 'IHYST':0, 'ILOS':0, 'IDAMG':0, 'INCOND':0, 
                      'ITRUSS':0, 'SL':0, 'Y0':0, 'Z0':0, 'ISTOP':0}
        rmk_line_3 = {'K1':0, 'K2':0, 'K3':0, 'K4':0, 'K5':0, 'K6':0, 'WGT':0, 
                      'RF':0, 'RT':0}
        
        if rmk_line_1['LABEL'] not in raw_strct_mmbr_props.keys():
            raw_strct_mmbr_props.update({rmk_line_1['LABEL'] : [rmk_line_1, 
                                         rmk_line_2, rmk_line_3]})
        else:
            prop_no = raw_strct_mmbr_props[rmk_line_1['LABEL']][0]['N']
            
        get_rmk_link_props.update({link_no : prop_no})
        
    return raw_strct_mmbr_props, get_rmk_link_props

def process_part_fix(part_fix_line, rmk_line_4):
    """ Check and modify the values of 'FJ1z', 'FJ2z', 'FJ1y', and 'FJ2y'. """
    # Convert kN-m/rad to rad/kN-m
    flexibility = ''
    if cfg.M3I in part_fix_line.keys() and cfg.M2I in part_fix_line.keys():
        J1z = round(1.0 / float(part_fix_line[cfg.M3I]), 4)
        J1y = round(1.0 / float(part_fix_line[cfg.M2I]), 4)
        rmk_line_4['FJ1z'] = J1z
        rmk_line_4['FJ1y'] = J1y
        flexibility += '1-Z={} 1-Y={} '.format(J1z, J1y)
    
    if cfg.M3J in part_fix_line.keys() and cfg.M2J in part_fix_line.keys():
        J2z = round(1.0 / float(part_fix_line[cfg.M3J]), 4)
        J2y = round(1.0 / float(part_fix_line[cfg.M2J]), 4)
        rmk_line_4['FJ2z'] = J2z
        rmk_line_4['FJ2y'] = J2y
        flexibility += '2-Z={} 2-Y={} '.format(J2z, J2y)
    
    if flexibility != '':
        add_sec_id = ', joint flexibility: [{}]'.format(flexibility)
        return rmk_line_4, add_sec_id
    else:
        return rmk_line_4, ''

def process_frm_release(frm_rel_line, line_mmbr_prop):
    """ This function appends the values of IPINZ and IPINY to the member prop. """
    IPINZ = 0; IPINY = 0; add_sec_id = ''
    
    if frm_rel_line[cfg.M3I] == cfg.yes_rel and frm_rel_line[cfg.M3J] == cfg.yes_rel:
        IPINZ = 3
        add_sec_id = ', pinned (major)'
    elif frm_rel_line[cfg.M3I] == cfg.yes_rel:
        IPINZ = 1
        add_sec_id = ', hinged-I (major)'
    elif frm_rel_line[cfg.M3J] == cfg.yes_rel:
        IPINZ = 2 
        add_sec_id = ', hinged-J (major)'
        
    if frm_rel_line[cfg.M2I] == cfg.yes_rel and frm_rel_line[cfg.M2J] == cfg.yes_rel:
        IPINY = 3
        add_sec_id += ', pinned (minor)'
    elif frm_rel_line[cfg.M2I] == cfg.yes_rel:
        IPINY = 1
        add_sec_id += ', hinged-I (minor)'
    elif frm_rel_line[cfg.M2J] == cfg.yes_rel:
        IPINY = 2
        add_sec_id += ', hinged-J (minor)'
    
    # Update the parameters concerning frame release
    line_mmbr_prop['IPINZ'] = IPINZ
    line_mmbr_prop['IPINY'] = IPINY
    
    return line_mmbr_prop, add_sec_id

def process_frm_offset(frm_off_line, line_mmbr_prop):
    """ This function appends the values of Y0 and Z0 to the member prop. """
    Y0 = frm_off_line[cfg.off_y]
    Z0 = frm_off_line[cfg.off_z]
    
    add_sec_id = ', offset: y={0} z={1}'.format(Y0, Z0)
    line_mmbr_prop['Y0'] = Y0
    line_mmbr_prop['Z0'] = Z0
    
    return line_mmbr_prop, add_sec_id

def txt_format(raw_strct_mmbr_props):
    """ This function creates a printable format that can be exported to a 
    txt file. """
    rmk_mmbr_props_txt = ''
    
    for prop in raw_strct_mmbr_props.values():
        for entry_val in prop[0].values():
            rmk_mmbr_props_txt += '{}\t'.format(entry_val)
            
        rmk_mmbr_props_txt += '\n'
        
        for line in prop[1:]:
            rmk_mmbr_props_txt += '\t'
            
            for entry_val in line.values():
                rmk_mmbr_props_txt += '{}\t'.format(entry_val)
                
            rmk_mmbr_props_txt += '\n'
        
    return rmk_mmbr_props_txt