# PMMA

Simulation of PMMA (poly-methyl methacrylate) in water or methanol 
using dissipative particle dynamics in [http://lammps.sandia.gov](LAMMPS),
with interaction parameters calculated from the Flory-Huggins theory.

The `gen_pmma.py` script generates a LAMMPS data file with initial setting (atomic coordinates
and bonds). This is then read with LAMMPS input file `pmma.in` typing 
```bash
$ mpirun -n 8 lmp_mpi < pmma.in
``` 
(using 8 cores), where `lmp_mpi` is the LAMMPS executable (on the PATH).

To produce the data file, the `input.yaml` file as provided is needed.
To start, run `gen_pmma.py -h`.


## Dependencies
* `sudo pip install numpy pyyaml docopt`


## Physics
[https://en.wikipedia.org/wiki/Hildebrand_solubility_parameter](Hildebrand solubility parameters) $delta$:
* water: 47.8
* methanol: 13.1
* PMMA: 19

Calculate the Flory-Huggins ksi parameters using
`ksi(i,j) = <Vm>/(RT) (delta(i) - delta(j))**2`
where `<Vm>` is average molar volume of the two constituents (e.g. PMMA and water)
