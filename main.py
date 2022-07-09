from s4sdk import Package, StringTable
from s4sdk.metadata import ResourceType
import os


if __name__ == "__main__":
    src_stbl = os.path.join("tests/assets/", "S4_220557DA_00000000_0054935F2685AD48%%+STBL.stbl")
    dest_csv = os.path.join("tests/assets/", "out.csv")
    dest_stbl = os.path.join("tests/assets/", "out.stbl")
    src_pkg = os.path.join("tests/assets/", "FontFix.package")
    dest_gfx = os.path.join("tests/assets/", "out.gfx")
    out_pkg = os.path.join("tests/assets/", "out.package")

    # Test import from STBL and from exported CSV
    stbl = StringTable.read(path=src_stbl)
    print(stbl.meta_data)
    stbl.write_csv(path=dest_csv)
    stbl.read_csv(path=dest_csv)
    print(stbl.meta_data)

    # Test export to STBL
    stbl.write(path=dest_stbl)

    # Test read exported STBL
    new = StringTable.read(path=dest_stbl)
    print(new.meta_data)

    pkg = Package.read(src_pkg)
    pkg.list()
    pkg.export(instance_id=6664397830470224506, path=dest_gfx)
    resource = pkg.get(instance_id=6664397830470224506)

    src_pkg = os.path.join("tests/assets/", "Strings_ENG_US.package")
    out_pkg = os.path.join("tests/assets/", "out2.package")

    pkg = Package.read(src_pkg)
    resource = pkg.get(instance_id=int("0054935F2685AD48", 16))
    new_pkg = Package.open(out_pkg, overwrite=True)
    new_pkg.insert(resource=resource)

    pass
