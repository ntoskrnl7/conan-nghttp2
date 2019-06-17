#!/usr/bin/env python
# -*- coding: utf-8 -*-


import copy
from bincrafters import build_template_default

if __name__ == "__main__":

    builder = build_template_default.get_builder()

    for item in copy.copy(builder.items):
        if item.settings["compiler"] == "Visual Studio":
            new_options = copy.copy(item.options)
            new_options["nghttp2:with_app"] = False
            new_options["nghttp2:with_hpack"] = False
            builder.add(settings=item.settings, options=new_options,
                        env_vars=item.env_vars, build_requires=item.build_requires)

    for item in copy.copy(builder.items):
        # add asio builds for specific configurations which do not miss dependencies
        # it will work with Visual Studio when with_app is False (conf added before)
        if (item.settings["compiler"] == "clang" and \
            item.settings["compiler.version"] == "7.0" and \
            item.settings["build_type"] == "Release") or \
           (item.settings["compiler"] == "Visual Studio" and \
             item.settings["compiler.version"] == "15" and \
             item.settings["build_type"] == "Release"):
            new_options = copy.copy(item.options)
            new_options["nghttp2:with_asio"] = True
            builder.add(settings=item.settings, options=new_options,
                        env_vars=item.env_vars, build_requires=item.build_requires)

    builder.run()
