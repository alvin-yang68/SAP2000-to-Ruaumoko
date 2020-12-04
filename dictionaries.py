# -*- coding: utf-8 -*-
"""
Created on Mon Jan 28 21:22:25 2019

@author: alvin
"""

import pickle

# Define helper functions
def load_data():
    """ This function loads the s2k to rmk nodes no. and members no., and the  
    props no. to members no. dictionaries. """
    try:
        file =  open('data.pickle', 'rb')
        dicts_container = pickle.load(file)[0]  # (s2k_to_rmk_nd, s2k_to_rmk_frm, 
                                                # s2k_to_rmk_link, prop_to_mmbr)
        file.close()
    except FileNotFoundError:
        print('data.pickle not found! Ensure that s2k_to_rmk.py is run first.')
    
    return dicts_container

def get_dict(dicts_container):
    """ Inquire the user to select the dictionary to use. """
    print('Select options:\n\n\t1. Convert rmk prop no. to rmk member no.\n' + 
          '\t2. Convert s2k frame ID to rmk member no.\n\t3. Convert s2k ' + 
          'link ID to rmk member no.\n\t4. Convert s2k joint ID to rmk ' + 
          'node no.\n\t5. Exit\n')
    user_choice = input('Enter selection [1]: ')
    
    while True:
        # Ensure that the user_input is valid and within the selection range
        if user_choice == '1' or user_choice == '':
            # Default case
            in_line = '\n[IN]\t' + 'rmk prop ID: '
            out_line = '\n[OUT]\t' + 'rmk member no.: '
            return dicts_container[0], in_line, out_line
        
        if user_choice == '2':
            in_line = '\n[IN]\t' + 's2k frame ID: '
            out_line = '\n[OUT]\t' + 'rmk member no.: '
            return dicts_container[1], in_line, out_line
        
        if user_choice == '3':
            in_line = '\n[IN]\t' + 's2k link ID: '
            out_line = '\n[OUT]\t' + 'rmk member no.: '
            return dicts_container[2], in_line, out_line
        
        if user_choice == '4':
            in_line = '\n[IN]\t' + 's2k joint ID: '
            out_line = '\n[OUT]\t' + 'rmk node no.: '
            return dicts_container[3], in_line, out_line
        
        if user_choice == '5':
            quit()
        
        user_choice = input('\nInvalid input! Try again: ')

# Define the main() function
def main():
    # Load the dictionaries and offer dictionary selection
    dicts_container = load_data()
    selected_dict, in_line, out_line = get_dict(dicts_container)
    
    # Run the corresponding dictionary and print the relevant values
    while True:
        dict_key = input(in_line)
        
        if dict_key != '':
            print('{0}{1}'.format(out_line, selected_dict[dict_key]))
        else:
            print('\n\n')
            selected_dict, in_line, out_line = get_dict(dicts_container)

# Run the main() function
if __name__ == '__main__':
    main()