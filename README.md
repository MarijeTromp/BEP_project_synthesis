# BEP_How_To_Train_Your_Dragon

This code is part of the [Research Project](https://github.com/TU-Delft-CSE/Research-Project)  21/22 Q4 at [TU Delft](https://https//github.com/TU-Delft-CSE) of M.R. Tromp (add your name here). The topics of the projects are:
- Alternatives to the components of a Genetic Algorithm (M.R. Tromp)
- Add your project


This codebase is an extension of the codebase provided for this research, which is called BEP_project_synthesis.

## BEP_project_synthesis

This code is part of the BEP projects of F. Azimzade, B. Jenneboer, N. Matulewicz, S. Rasing and V. van Wieringen.

### Source of training/test data
Robot and Pixel test/training data was generated by A. Cropper and S. Dumančić for their paper "Learning large logic programs by going beyond entailment." arXiv preprint arXiv:2004.09855 (2020).

The String test/training data was received from S. Dumančić who took them from the paper by Lin, Dianhuan, et al. "Bias reformulation for one-shot function induction." (2014).


## Genetic Algorithms
The code for this project is located in search/gen_prog/vanilla_GP_alternatives. The original code for VanillaGP is called vanilla_GP.py. 

To run the alternatives code, make sure that main.py contains [VanillaGPReworked, "gpr"] in the list of search algorithms.
If you want to change which alternatives are used, change <component>_type to the wanted alternative. 
Any other settings were kept the same as in the original VanillaGP, but can be changed. 

The results and processing of the results are located in search/gen_prog/vanilla_GP_alternatives/results_and_processing.
