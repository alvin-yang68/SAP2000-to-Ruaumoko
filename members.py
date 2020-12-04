# -*- coding: utf-8 -*-
"""
members.py: The s2k frames to rmk members convert module, which  defines the 
functions required to perform conversion, as well as other utilities. The class 
definitions for Beams and Columns are also  defined in this module.
"""

import config as cfg
from config import data_retriever

def convert(s2k_data, nodes_instances, weight_instances, get_rmk_props_no):
    """
    Converts the s2k frame connectivity to rmk member geometry. This is the 
    main function of this module which executes the other functions.
    """
    mmbr_no = 0     # Used to keep track of the rmk member no.
    
    # Get the rmk_mmbr_geo for gravity columns
    raw_grav_col, mmbr_no = get_grav_col_geo(weight_instances, mmbr_no)
    
    # Get the complete s2k_to_rmk_nd from StoreyNodes instances
    s2k_to_rmk_nd = {}
    
    for stry_nds_inst in nodes_instances.values():
        s2k_to_rmk_nd.update(stry_nds_inst.s2k_to_rmk_nd)
    
    # Get the rmk_mmbr_geo for beam/column members
    raw_beam_col_geo, mmbr_no, beams_instances, cols_instances = get_beam_col_geo(
            s2k_data, nodes_instances, s2k_to_rmk_nd, get_rmk_props_no['frame'], 
            mmbr_no)
    
    # Get the rmk_mmbr_geo for link members
    raw_link_geo, mmbr_no, links_instances= get_link_geo(
            s2k_data, nodes_instances, s2k_to_rmk_nd, get_rmk_props_no['link'], 
            mmbr_no)
    
    # Create a printable outputs in rmk format for rmk_mmbr_geo
    rmk_mmbr_geo_txt = (txt_format(raw_grav_col) + txt_format(raw_beam_col_geo) + 
                        txt_format(raw_link_geo))
    
    return rmk_mmbr_geo_txt, beams_instances, cols_instances, links_instances

def get_grav_col_geo(weight_instances, mmbr_no):
    """ Generate the gravity columns geometry. """
    raw_grav_col = {}
    
    for weight_inst in weight_instances:
        if weight_inst.diaph_idx == 0: continue
        
        mmbr_no += 1
        frm_id = 'GravCol {}'.format(weight_inst.diaph_idx)
        nd_k = weight_inst.nd_k
        nd_l = weight_inst.nd_l
        
        raw_grav_col.update({frm_id : {'N':mmbr_no, 'MTYPE':1, 'I':nd_k, 'J':nd_l, 
                                       'K':0, 'L':0, 'M':'Z', 'IOUT':0, 
                                       'LTYPE':0}})
    
    return raw_grav_col, mmbr_no

def get_beam_col_geo(s2k_data, nodes_instances, s2k_to_rmk_nd, 
                     get_rmk_frm_props, mmbr_no):
    """ Converts the s2k frames connectivity to beams and columns geometry """
    raw_strct_beam_col_geo = {}
    
    beams_instances = {}        # {unique height : a StoreyBeams instance}
    cols_instances = {}         # {unique coords : a Columns instance}
    
    # Organize the local axes assignment for use later
    s2k_loc_axs = data_retriever(s2k_data, cfg.title_frm_lcl_axs)
    get_loc_axs = {line[cfg.frame_axs] : line[cfg.angle] for line in s2k_loc_axs}
    
    # Organize the frame connectivity for use later
    s2k_frm_conn = data_retriever(s2k_data, cfg.title_frame_conn)
    
    # Converts the member geometry (beams and columns) from s2k to rmk format
    for line in s2k_frm_conn:
        # Group the members in terms of their storey or as column
        nd_k = s2k_to_rmk_nd[line[cfg.joint_i]]     # Joint i (origin)
        nd_l = s2k_to_rmk_nd[line[cfg.joint_j]]     # Joint j
        prop_no = get_rmk_frm_props[line[cfg.frame_conn]]
        
        if line[cfg.frame_conn] in get_loc_axs.keys():
            # Get the local axis 2 angle if local axis 2 is rotated
            angle = int(get_loc_axs[line[cfg.frame_conn]])
        else:
            angle = 0
        
        for height, stry_nds_inst in nodes_instances.items():
            # Find which storey joints i and j belongs to
            stry_ndl_data = stry_nds_inst.stry_data
            
            if nd_k in stry_ndl_data.keys() and nd_l in stry_ndl_data.keys():
                # Following lines deal with beam members
                if height not in beams_instances.keys():
                    # Self update the StoreyBeams instances container
                    beams_instances.update({height : StoreyBeams(height)})
                
                    # Set the member data of this beam member
                beams_instances[height].set_mmbr_data(line[cfg.frame_conn], 
                              prop_no, angle, nd_k, stry_ndl_data[nd_k], nd_l, 
                              stry_ndl_data[nd_l])
            elif nd_k in stry_ndl_data.keys():
                # Following lines deal with column members
                    # Get horizontal coords of the column: (x,z)
                col_coords = (stry_ndl_data[nd_k]['X'], stry_ndl_data[nd_k]['Z'])
                
                if col_coords not in cols_instances.keys():
                    # Self update the Columns instance container
                    cols_instances.update({col_coords : Columns(col_coords)})
                
                    # Set the member data of this column member
                cols_instances[col_coords].set_mmbr_data(line[cfg.frame_conn], 
                             prop_no, angle, nd_k, nd_l, height)
        
    # Generate the rmk_beam_geo and updates mmbr_no
    for stry_beam_inst in beams_instances.values():
        mmbr_no = stry_beam_inst.refine_mmbr_data(mmbr_no)
        raw_strct_beam_col_geo.update(stry_beam_inst.raw_stry_beam_geo)
        
    # Generate the rmk_col_geo and updates mmbr_no
    for col_inst in cols_instances.values():
        mmbr_no = col_inst.refine_mmbr_data(mmbr_no)
        raw_strct_beam_col_geo.update(col_inst.rmk_col_geo)
    
    return raw_strct_beam_col_geo, mmbr_no, beams_instances, cols_instances

def get_link_geo(s2k_data, nodes_instances, s2k_to_rmk_nd, 
                 get_rmk_link_props, mmbr_no):
    """ Converts the s2k links connectivity to member geometry """
    raw_strct_link_geo = {}
    
    links_instances = {}        # {unique height : a Links instance}
    
    # Organize the local axes assignment for use later
    s2k_loc_axs = data_retriever(s2k_data, cfg.title_link_lcl_axs)
    get_loc_axs = {line[cfg.link_axs] : line[cfg.angle] for line in s2k_loc_axs}
    
    # Organize the link connectivity for use later
    s2k_link_conn = data_retriever(s2k_data, cfg.title_link_conn)
    
    # Converts the member geometry (links) from s2k to rmk format
    for line in s2k_link_conn:
        # Group the members in terms of their storey or as column
        nd_k = s2k_to_rmk_nd[line[cfg.joint_i]]
        nd_l = s2k_to_rmk_nd[line[cfg.joint_j]]
        prop_no = get_rmk_link_props[line[cfg.link_conn]]
        
        if line[cfg.link_conn] in get_loc_axs.keys():
            # Get the local axis 2 angle if local axis 2 is rotated
            angle = int(get_loc_axs[line[cfg.link_conn]])
        else:
            angle = 0
        
        for height, stry_nds_inst in nodes_instances.items():
            # Find which storey joints i and j belongs to
            stry_ndl_data = stry_nds_inst.stry_data
            
            if nd_k in stry_ndl_data.keys():
                if height not in links_instances.keys():
                    # Self update the StoreyBeams instances container
                    links_instances.update({height : Links(height)})
                    
                    # Set the member data of this beam member
                if nd_l not in stry_ndl_data.keys():
                    links_instances[height].set_mmbr_data(line[cfg.link_conn], 
                                   prop_no, angle, nd_k, stry_ndl_data[nd_k], nd_l, 
                                   stry_ndl_data[nd_k])
                else:
                    links_instances[height].set_mmbr_data(line[cfg.link_conn], 
                                   prop_no, angle, nd_k, stry_ndl_data[nd_k], nd_l, 
                                   stry_ndl_data[nd_l])
                
    # Generate the rmk_link_geo and updates mmbr_no
    for stry_link_inst in links_instances.values():
        mmbr_no = stry_link_inst.refine_mmbr_data(mmbr_no)
        raw_strct_link_geo.update(stry_link_inst.rmk_stry_link_geo)
    
    return raw_strct_link_geo, mmbr_no, links_instances

def txt_format(rmk_strct_mmbr_geo):
    """ This function creates a printable format that can be exported to a 
    txt file """
    rmk_mmbr_geo_txt = ''
    
    for line in rmk_strct_mmbr_geo.values():
        txt_1 = '{0}\t{1}\t{2}\t{3}\t{4}\t'.format(
                line['N'], line['MTYPE'], line['I'], line['J'], line['K'])
        txt_2 = '{0}\t{1}\t{2}\t{3}\n'.format(
                line['L'], line['M'], line['IOUT'], line['LTYPE'])
        
        rmk_mmbr_geo_txt += txt_1 + txt_2
    
    return rmk_mmbr_geo_txt

def get_dictionaries(beams_instances, cols_instances, links_instances):
    """ This function returns the dictionaries: prop_to_mmbr, s2k_to_rmk_frm, 
    and s2k_to_rmk_link """
    prop_to_mmbr = {}
    s2k_to_rmk_frm = {}
    s2k_to_rmk_link = {}
    
    for stry_beam_inst in beams_instances.values():
        s2k_to_rmk_frm.update(stry_beam_inst.s2k_to_rmk_beam)
        prop_to_mmbr.update(stry_beam_inst.prop_to_mmbr)
        
    for col_inst in cols_instances.values():
        s2k_to_rmk_frm.update(col_inst.s2k_to_rmk_col)
        prop_to_mmbr.update(col_inst.prop_to_mmbr)
        
    for stry_link_inst in links_instances.values():
        s2k_to_rmk_link.update(stry_link_inst.s2k_to_rmk_link)
        prop_to_mmbr.update(stry_link_inst.prop_to_mmbr)
        
    return prop_to_mmbr, s2k_to_rmk_frm, s2k_to_rmk_link

class StoreyBeams:
    """
    A StoreyBeams instance groups all the beam members data in a storey of the 
    structure. The beams_data dictionary contains all the coordinates of each 
    beam in the instance.
    """
    def __init__(self, height):
        """ Initializer with a 'height' and storey member data parameter to 
        inform the storey height of these instances. """
        self.height = height
        
        self.raw_stry_beam_geo = {}
        self.beams_data = {} # {rmk member no. : {coords of nd k, coords of nd l}}
        
        self.s2k_to_rmk_beam = {}   # {s2k frame ID : rmk member no.}
        self.prop_to_mmbr = {}      # {rmk prop no. : rmk member no.}
        
    def __str__(self):
        """ For print() and str() """
        return 'This instance has a height of: {:.2f}'.format(self.height)
    
    def __repr__(self):
        """ For repr() and interactive prompt """
        return 'StoreyBeams(height={})'.format(self.height)
    
    def set_mmbr_data(self, frm_id, prop_no, angle, nd_k, coords_k, nd_l, coords_l):
        """ This function sets all the beam member data except the frame ID 
        into the rmk format """
        M = self.convert_lcl_axs(angle, coords_k, coords_l, frm_id)
        
        self.raw_stry_beam_geo.update({frm_id : {'N':None, 'MTYPE':prop_no, 
                                                 'I':nd_k, 'J':nd_l, 'K':0, 
                                                 'L':0, 'M':M, 'IOUT':0, 
                                                 'LTYPE':0}})
        
            # Update the storey data for use in plotting or as reference later
        coords_k = (coords_k['X'], coords_k['Z'])       # (x,z)
        coords_l = (coords_l['X'], coords_l['Z'])       # (x,z)
        
        self.s2k_to_rmk_beam.update({frm_id : {'K':coords_k, 'L':coords_l}})
        
        if prop_no not in self.prop_to_mmbr.keys():
            self.prop_to_mmbr.update({str(prop_no) : []})
    
    def refine_mmbr_data(self, mmbr_no):
        """ Define the rmk member ID by enumerating rmk_strct_mmbr_geo """
        for frm_id in self.raw_stry_beam_geo.keys():
            mmbr_no += 1
            self.raw_stry_beam_geo[frm_id]['N'] = mmbr_no
            
            jnt_coords = self.s2k_to_rmk_beam[frm_id]
            self.beams_data.update({mmbr_no : jnt_coords})
            self.s2k_to_rmk_beam[frm_id] = mmbr_no
            
            prop_no = str(self.raw_stry_beam_geo[frm_id]['MTYPE'])
            self.prop_to_mmbr[prop_no].append(mmbr_no)
        
        return mmbr_no
    
    def convert_lcl_axs(self, angle, coords_k, coords_l, frm_id):
        """ Convert the s2k angle of local axis 2 to rmk node M position """
        if angle == 0:
            # Major axis is horizontal
            if coords_k['X'] == coords_l['X']:
                # Beam spans along global Z-axis
                return 'X'
            elif coords_k['Z'] == coords_l['Z']:
                # Beam spans along global X-axis
                return 'Z'
            else:
                # Beam is neither parallel to global Z or X axis
                if (coords_l['Z'] - coords_k['Z']) > 0: return 'X'
                if (coords_l['Z'] - coords_k['Z']) < 0: return '-X'
        elif abs(angle) == 180:
            # Major axis is horizontal, but sect mirrored about horizontal axis
            if coords_k['X'] == coords_l['X']:
                return '-X'
            elif coords_k['Z'] == coords_l['Z']:
                return '-Z'
            else:
                if (coords_l['Z'] - coords_k['Z']) > 0: return '-X'
                if (coords_l['Z'] - coords_k['Z']) < 0: return 'X'
        elif angle == 90:
            # Major axis is vertical
            return '-Y'
        elif angle == -90:
            # Major axis is vertical
            return 'Y'
        else:
            info = '{0} at height of {1}'.format(frm_id, self.height)
            print('Invalid local axis angle for frame (beam) ' + info +
                  '! Edit section properties to simulate torsional ' + 
                  'eccentricity instead...')
            return None
    
class Columns:
    """
    A Columns instance groups all the column members at each storey along the 
    height of the structure. The cols_data dictionary contains the height of 
    node k (origin) of each column section in the instance.
    """
    def __init__(self, coords):
        """ Initializer with a 'coords' and storey member data parameter to 
        inform the column coordinates [x,z] of these instances. """
        self.coords = coords        # A tuple containing (x,z)
        
        self.rmk_col_geo = {}
        self.cols_data = {}         # {rmk member no. : height of node k}
        
        self.s2k_to_rmk_col = {}    # {s2k frame ID : rmk member no.}
        self.prop_to_mmbr = {}      # {rmk prop no. : rmk member no.}
        
    def __str__(self):
        """ For print() and str() """
        return 'This instance has coordinates (x,z) of: {:.2f}'.format(
                self.coords)
    
    def __repr__(self):
        """ For repr() and interactive prompt """
        return 'Columns(coords={})'.format(self.coords)
    
    def set_mmbr_data(self, frm_id, prop_no, angle, nd_k, nd_l, height_k):
        """ This function sets all the column member data except the frame ID 
        into the rmk format """
        
        M = self.convert_lcl_axs(angle, frm_id)
        
        self.rmk_col_geo.update({frm_id : {'N':None, 'MTYPE':prop_no, 'I':nd_k, 
                                           'J':nd_l, 'K':0, 'L':0, 'M':M, 
                                           'IOUT':0, 'LTYPE':0}})
        
        self.s2k_to_rmk_col.update({frm_id : height_k})
        
        if prop_no not in self.prop_to_mmbr.keys():
            self.prop_to_mmbr.update({str(prop_no) : []})
    
    def refine_mmbr_data(self, mmbr_no):
        """ Define the rmk member ID by enumerating rmk_strct_mmbr_geo """
        for frm_id in self.rmk_col_geo.keys():
            mmbr_no += 1
            self.rmk_col_geo[frm_id]['N'] = mmbr_no
            
            col_height = self.s2k_to_rmk_col[frm_id]
            self.cols_data.update({mmbr_no : col_height})
            self.s2k_to_rmk_col.update({frm_id : mmbr_no})
            
            prop_no = str(self.rmk_col_geo[frm_id]['MTYPE'])
            self.prop_to_mmbr[prop_no].append(mmbr_no)
        
        return mmbr_no
    
    def convert_lcl_axs(self, angle, frm_id):
        """ Convert the s2k angle of local axis 2 to rmk node M position. 
        Assuming that the column section is symmetrical about its major axis """
        if angle == 0 or abs(angle) == 180:
            return 'Z'
        elif abs(angle) == 90:
            return 'X'
        else:
            info = '{0} at (x={1}, y={2})'.format(frm_id, self.coords[0], 
                    self.coords[1])
            print('Invalid local axis angle for frame (column) ' + info +
                  '! Edit section properties to simulate torsional ' + 
                  'eccentricity instead...')
            return None
        
class Links:
    """
    A Links instance groups all the link members data with the same node k 
    (origin) coordinates. The links_data dictionary contains the coordinates of 
    each link in the instance.
    """
    def __init__(self, height):
        """ Initializer with a 'height' and storey member data parameter to 
        inform the storey height of these instances. """
        self.height = height
        
        self.rmk_stry_link_geo = {}
        self.links_data = {} # {rmk member no. : {coords of nd k, coords of nd l}}
        
        self.s2k_to_rmk_link = {}    # {s2k frame ID : rmk member no.}
        self.prop_to_mmbr = {}      # {rmk prop no. : rmk member no.}
        
    def __str__(self):
        """ For print() and str() """
        return 'This instance has a node k height of: {:.2f}'.format(self.height)
    
    def __repr__(self):
        """ For repr() and interactive prompt """
        return 'Links(height={})'.format(self.height)
    
    def set_mmbr_data(self, frm_id, prop_no, angle, nd_k, coords_k, nd_l, coords_l):
        """ This function sets all the beam member data except the frame ID 
        into the rmk format """
        M = self.convert_lcl_axs(angle, coords_k, coords_l, frm_id)
        
        self.rmk_stry_link_geo.update({frm_id : {'N':None, 'MTYPE':prop_no, 
                                                 'I':nd_k, 'J':nd_l, 'K':0, 
                                                 'L':0, 'M':M, 'IOUT':0, 
                                                 'LTYPE':0}})
        
            # Update the storey data for use in plotting or as reference later
        coords_k = (coords_k['X'], coords_k['Z'])       # (x,z)
        coords_l = (coords_l['X'], coords_l['Z'])       # (x,z)
        
        self.s2k_to_rmk_link.update({frm_id : {'K':coords_k, 'L':coords_l}})
        
        if prop_no not in self.prop_to_mmbr.keys():
            self.prop_to_mmbr.update({str(prop_no) : []})
    
    def refine_mmbr_data(self, mmbr_no):
        """ Define the rmk member ID by enumerating rmk_strct_mmbr_geo """
        for frm_id in self.rmk_stry_link_geo.keys():
            mmbr_no += 1
            self.rmk_stry_link_geo[frm_id]['N'] = mmbr_no
            
            jnt_coords = self.s2k_to_rmk_link[frm_id]
            self.links_data.update({mmbr_no : jnt_coords})
            self.s2k_to_rmk_link[frm_id] = mmbr_no
        
        prop_no = str(self.rmk_stry_link_geo[frm_id]['MTYPE'])
        self.prop_to_mmbr[prop_no].append(mmbr_no)
        
        return mmbr_no
    
    def convert_lcl_axs(self, angle, coords_k, coords_l, frm_id):
        """ Convert the s2k angle of local axis 2 to rmk node M position """
        if angle == 0 or abs(angle) == 180:
            return 'Z'
        elif abs(angle) == 90:
            return 'X'
        else:
            info = '{0} at (x={1}, y={2})'.format(frm_id, self.coords[0], 
                    self.coords[1])
            print('Invalid local axis angle for frame (column) ' + info +
                  '! Edit section properties to simulate torsional ' + 
                  'eccentricity instead...')
            return None
#        if angle == 0:
#            # Major axis is horizontal
#            if coords_k['X'] == coords_l['X']:
#                # Beam spans along global Z-axis
#                return 'X'
#            elif coords_k['Z'] == coords_l['Z']:
#                # Beam spans along global X-axis
#                return 'Z'
#            else:
#                # Beam is neither parallel to global Z or X axis
#                if (coords_l['Z'] - coords_k['Z']) > 0: return 'X'
#                if (coords_l['Z'] - coords_k['Z']) < 0: return '-X'
#        elif abs(angle) == 180:
#            # Major axis is horizontal, but sect mirrored about horizontal axis
#            if coords_k['X'] == coords_l['X']:
#                return '-X'
#            elif coords_k['Z'] == coords_l['Z']:
#                return '-Z'
#            else:
#                if (coords_l['Z'] - coords_k['Z']) > 0: return '-X'
#                if (coords_l['Z'] - coords_k['Z']) < 0: return 'X'
#        elif angle == 90:
#            # Major axis is vertical
#            return '-Y'
#        elif angle == -90:
#            # Major axis is vertical
#            return 'Y'
#        else:
#            info = '{0} at height of {1}'.format(frm_id, self.height)
#            print('Invalid local axis angle for link ' + info +
#                  '! Edit section properties to simulate torsional ' + 
#                  'eccentricity instead...')
#            return None