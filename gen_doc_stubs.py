# Generates virtual doc files for the mkdocs site.
# You can also run this script directly to actually write out those files, as a preview.

import mkdocs_gen_files

root = mkdocs_gen_files.config['plugins']['mkdocstrings'].get_handler('crystal').collector.root

for typ in root.lookup("Athena").walk_types():
    # Athena::Validator::Violation -> Validator/Violation/index.md
    filename = '/'.join(typ.abs_id.split('::')[1:] + ['index.md'])

    with mkdocs_gen_files.open(filename, 'w') as f:
        # Write the entry of a top-level alias (e.g. `AED`) on the same page as the aliased item.
        for root_typ in root.types:
            if root_typ.kind == "alias":
                if root_typ.aliased == typ.abs_id:
                    f.write(f'# ::: {root_typ.abs_id}\n\n---\n\n')

        # Other special top-level entries that don't have their dedicated page.
        if typ.abs_id == "Athena::Config":
            f.write(f'# ::: Athena\n\n---\n\n')
        elif typ.abs_id == "Athena::Validator":
            f.write(f'# ::: Assert\n\n---\n\n')

        # The actual main entry of the page.
        f.write(f'# ::: {typ.abs_id}\n\n')

    if typ.locations:
        mkdocs_gen_files.set_edit_path(filename, typ.locations[0].url)
