import numpy as np
import matplotlib.pyplot as plt
import lime
from lime import lime_tabular

import config

def save_lime_explanation(exp, instance_loc, model_name, position):

    # exp.show_in_notebook(show_table=True)
    # Save as html file
    exp.save_to_file(f'{config.LIME_DEST}{position}/lime_exp_{instance_loc}_{model_name}.html')

    # Save as pyplot figure
    plt.cla()
    exp.as_pyplot_figure()
    plt.savefig(f'{config.LIME_DEST}lime_exp_{instance_loc}_{model_name}.png')
    plt.show()

    return

def get_lime_explanation(x_train, x_test, top_instance_loc_list, bottom_instance_loc_list, class_names, mode, model, model_name):

    #! take the list of instances and save the explaination of each instance.
    # LIME: define the explainer
    # Ex: mode = 'classification' or 'regression'
    #     class_names = ['0', '1']
    
    
    explainer_lime = lime_tabular.LimeTabularExplainer(
        training_data=np.array(x_train),
        feature_names=x_train.columns,
        class_names=class_names,
        mode=mode
    )
    
    
    for instance_loc in top_instance_loc_list:
        # Select instance and explain
        instance = x_test.iloc[instance_loc]
        exp1 = explainer_lime.explain_instance(
            data_row=instance,
            predict_fn=model.predict_proba
        )
        # Save the explanation as a figure
        save_lime_explanation(exp1, instance_loc, model_name, "top")
        
    for instance_loc in bottom_instance_loc_list:
        # Select instance and explain
        instance = x_test.iloc[instance_loc]
        exp2 = explainer_lime.explain_instance(
            data_row=instance,
            predict_fn=model.predict_proba
        )
        # Save the explanation as a figure
        save_lime_explanation(exp2, instance_loc, model_name, "bottom")

    # return exp



