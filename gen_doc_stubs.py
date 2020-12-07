import mkdocs_gen_files

root = mkdocs_gen_files.config['plugins']['mkdocstrings'].get_handler('crystal').collector.root

for typ in root.lookup("Athena").walk_types():
    # Athena::Validator::Violation -> Validator/Violation/index.md
    filename = '/'.join(typ.abs_id.split('::')[1:] + ['index.md'])

    with mkdocs_gen_files.open(filename, 'w') as f:
        for root_typ in root.types:
            if root_typ.kind == "alias":
                if root_typ.aliased == typ.abs_id:
                    f.write(f'::: {root_typ.abs_id}\n\n')

        if typ.abs_id == "Athena::Config":
            f.write(f'::: Athena\n\n')
        elif typ.abs_id == "Athena::Validator":
            f.write(f'::: Assert\n\n')

        f.write(f'::: {typ.abs_id}\n\n')
