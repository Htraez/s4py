from s4py.stbl import StringTable
import os


if __name__ == "__main__":
    src_stbl = os.path.join("tests/assets/", "S4_220557DA_00000000_0054935F2685AD48%%+STBL.stbl")
    dest_csv = os.path.join("tests/assets/", "out.csv")
    dest_stbl = os.path.join("tests/assets/", "out.stbl")

    # Test import from STBL and from exported CSV
    stbl = StringTable.from_stbl(stbl_path=src_stbl)
    print(stbl.meta_data)
    stbl.as_csv(path=dest_csv)
    stbl.from_csv(path=dest_csv)
    print(stbl.meta_data)

    # Test export to STBL
    stbl.as_stbl(path=dest_stbl)

    # Test read exported STBL
    new = StringTable.from_stbl(stbl_path=dest_stbl)
    print(new.meta_data)
