# UncompressedJson2Angeldust
A converter of Uncompressed Json from [obj2schematic](https://objtoschematic.com/) to the [Angeldust](angeldu.st) chunk file.
# Quick tutorial
- Upload an .obj file to the site, maybe you should rotate 90° in the x axis,  and then set the materials. Set the the constrait axis to z and chosse the voxel size should be lower than 63.
After assing the blocks export as uncompressed Json and Run the software.
- Select the file and define the output file, as default it will create a folder named "output_chunks" in the same folder as the script/executable but you can set a custom path to the Angeldust folder, "AppData\Roaming\Metagaming B.V\Angeldust"
- Convert, if is everything okay it should give a message if not try reduncing the size or changing the constrait axis


# Acknowledgements
- Credits to obi for the base chunk saving and loading functionality.
- [Lucas Dower](https://github.com/LucasDower) for the obj2schematic.
