import re

import value

def parse_eos_query(raw_query) -> dict:
    """Take a raw eos query and break it into component parts"""
    # Check how many slashes are in the raw query to determine the format
    slash_count = raw_query.count("/")
    separated_query = raw_query.split("/")
    print(separated_query)
    if separated_query[0] == "":
        # Extra slash was added at the front, ignore it and decrease slash count
        separated_query = separated_query[1:]
        slash_count -= 1

    if slash_count == 2:
        # No frame provided
        frame_type = None
        frame_target = None
        target_type = separated_query[0]
        raw_target = separated_query[1]
        target = raw_target.split(":")
        attribute = separated_query[2]
    elif slash_count == 4:
        # Frame provided
        frame_type = separated_query[0]
        frame_target = separated_query[1]
        target_type = separated_query[2]
        raw_target = separated_query[3]
        target = raw_target.split(":")
        attribute = separated_query[4]
    else:
        # Improperly formatted query, return None
        return None

    return {"frame_type": frame_type, "frame_target": frame_target, "target_type": target_type, "target": target,
            "attribute": attribute}


def parse_multiple_targets(target_list):
    """Parse a string containing at least one target, and return all targets in range"""
    if isinstance(target_list, list):
        target_list = str(target_list[0])

    print("Target list: ", target_list)

    # Get the number/operator pairs from the target list.
    # The regex below selects a whole number or float, optionally followed by a colon and another
    # whole number or float, (and another colon/number combo), then optionally (but greedily) a +, -, or >.
    target_numbers = re.findall("(?:\d+)(?:\.\d+)?(?::(?:\d+)(?:\.\d+)?)?(?::(?:\d+)(?:\.\d+)?)?[+->]?", target_list)
    print("Target numbers: ", target_numbers)

    # Split the operators off of the numbers
    target_pairs = []
    for pair in target_numbers:
        if pair[-1] in [">", "+", "-"]:
            target_pairs.append([pair[0:-1], pair[-1]])
        else:
            # Last target in selection
            target_pairs.append([pair, ""])

    print("Target pairs: ", target_pairs)

    # If target_list is actually one number, just return it as is
    if len(target_pairs) == 1:
        return [target_list]

    target_buffer = []
    for i in range(len(target_pairs)):
        if target_pairs[i][1] == ">":
            start_of_thru = target_pairs[i][0]
            end_of_thru = target_pairs[i+1][0]

            # Interpolate numbers in between
            in_between_targets = list(range(int(start_of_thru), int(end_of_thru)))[1:]
            thru_range = [start_of_thru]

            for target in in_between_targets:
                thru_range.append(str(target))

            thru_range.append(end_of_thru)
            target_buffer.append(thru_range)
        else:
            # Placeholders for + and -
            target_buffer.append([])

    buffer_indices_to_delete = []
    for i in range(len(target_pairs)):
        if target_pairs[i][1] == "+":
            if i > 0 and ((i + 1) != len(target_pairs)):
                if target_pairs[i-1][1] == ">" and target_pairs[i+1][1] == ">":
                    # We're adding two lists together
                    # Join the two lists in the target buffer
                    target_buffer[i-1] = list(set(target_buffer[i-1] + target_buffer[i+1]))

                    # Add + placeholder and second list to list of indices to remove
                    buffer_indices_to_delete.append(i)
                elif target_pairs[i-1][1] == ">":
                    # We're adding a single channel to the list
                    target_buffer[i - 1] = list(set(target_buffer[i - 1] + [target_pairs[i + 1][0]]))
                    # Add +/- placeholder to list of indices to delete
                    buffer_indices_to_delete.append(i)
                    buffer_indices_to_delete.append(i + 1)
                else:
                    # Last thing was just an add or subtract single target, find the most recent list and add to that
                    reverse_index_count = i
                    list_not_found = True
                    while list_not_found and reverse_index_count >= 0:
                        if len(target_buffer[reverse_index_count]) > 0:
                            target_buffer[reverse_index_count] = list(set(target_buffer[reverse_index_count] + target_pairs[i + 1][0]))
                            list_not_found = False
                        else:
                            reverse_index_count -= 1

        elif target_pairs[i][1] == "-":
            if target_pairs[i - 1][1] == ">" and target_pairs[i + 1][1] == ">":
                # We're subtracting one list from another
                # Remove targets in the second set from the first set
                common_targets = list(set(target_buffer[i - 1]) & set(target_buffer[i + 1]))
                amended_targets = []
                for target in target_buffer[i - 1]:
                    if target not in common_targets:
                        amended_targets.append(target)

                target_buffer[i - 1] = amended_targets
                # Add - placeholder and second list to list of indices to remove
                buffer_indices_to_delete.append(i)
                buffer_indices_to_delete.append(i + 1)
            elif target_pairs[i - 1][1] == ">":
                # We're subtracing a single target from the overall list
                print("Removing ", target_pairs[i - 1][0])
                for sub_list in target_buffer:
                    try:
                        sub_list.remove(target_pairs[i + 1][0])
                    except ValueError:
                        pass

                # Add - placeholder to list of indices to delete
                buffer_indices_to_delete.append(i)
                buffer_indices_to_delete.append(i + 1)

            elif target_pairs[i + 1][1] == ">":
                # We're subtracing a list from the overall list
                print("Removing ", target_pairs[i - 1][0])
                for sub_list in target_buffer:
                        for element in target_buffer[i + 1]:
                            try:
                                sub_list.remove(element)
                            except ValueError:
                                pass

                # Add - placeholder to list of indices to delete
                buffer_indices_to_delete.append(i)
                buffer_indices_to_delete.append(i + 1)
            else:
                # Last thing was just an add or subtract single target, remove this from all lists
                print("Remvoing from all lists")
                for sub_list in target_buffer:
                    try:
                        sub_list.remove(target_pairs[i + 1][0])
                    except ValueError:
                        pass
        elif target_pairs[i][1] == "":
            # End of target list, Everything should be taken care of
            # buffer_indices_to_delete.append(i)
            pass
        print(target_buffer)
        print(buffer_indices_to_delete)

    print("Raw target buffer: ", target_buffer)
    print("Indices to remove: ", buffer_indices_to_delete)

    final_target_buffer = []
    for i in range(len(target_buffer)):
        print(i, buffer_indices_to_delete)
        if i not in buffer_indices_to_delete:
            final_target_buffer.append(target_buffer[i])

    print("Final target buffer: ", final_target_buffer)
    # Merge all remaining lists in the final target buffer
    mega_list = []
    for i in final_target_buffer:
        mega_list = mega_list + i

    target_list = list(set(mega_list))
    print(target_list)

    return target_list

def get_setup_osc(frame_type, frame_target):
    """Based on the given frame type and target, return a list of OSC commands to send to set up a query."""
    """if frame_type is None or frame_target is None:
        return [["", []]]
    elif frame_type == "cue":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/cue/%s" % frame_target, []]]
    elif frame_type == "ip":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/ip/%s" % frame_target, []]]
    elif frame_type == "cp":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/cp/%s" % frame_target, []]]
    elif frame_type == "fp":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/fp/%s" % frame_target, []]]
    elif frame_type == "bp":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/bp/%s" % frame_target, []]]
    elif frame_type == "sub":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/sub/%s" % frame_target, []]]
    elif frame_type == "preset":
        pass
    else:
        return [["", []]]"""
    # Frames do not seem like they're going to work, as Eos doesn't send the data for fixtures as they are in blind.
    # I'm leaving this here in the hopes that they will one day!
    return [["", []]]


def get_cleanup_osc(frame_type, frame_target):
    """Based on the given frame type and target, return a list of OSC commands to send to cleanup a query."""
    """if frame_type is None or frame_target is None:
        return [["", []]]
    elif frame_type == "cue":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/cue/%s" % frame_target, []]]
    elif frame_type == "ip":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/ip/%s" % frame_target, []]]
    elif frame_type == "cp":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/cp/%s" % frame_target, []]]
    elif frame_type == "fp":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/fp/%s" % frame_target, []]]
    elif frame_type == "bp":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/bp/%s" % frame_target, []]]
    elif frame_type == "sub":
        return [["/eos/user/0/cmd/blind", []], ["/eos/user/0/sub/%s" % frame_target, []]]
    elif frame_type == "preset":
        pass
    else:
        return [["", []]]"""
    # Frames do not seem like they're going to work, as Eos doesn't send the data for fixtures as they are in blind.
    # I'm leaving this here in the hopes that they will one day!
    return [["", []]]


def get_query_osc(target_type: str, target_list: list, attribute: str):
    """Based on the target type, target list, and attribute, return an OSC address and response to get the information."""
    # Check if any items in the target list are multi-part. If they are, split them into their component parts.
    split_target_list = []
    try:
        for target in target_list:
            split_target_list.append(target.split(":"))
    except TypeError:
        # Target was invalid, return None
        return None

    target_list = split_target_list


    # The address pattern to send to get the query's requested info
    osc_query_address_pattern = None

    # The response from the console which should trigger the internal macro which will accept the query response.
    # Format: ["osc_address_pattern_with_optional_wildcards", ["regex_for_relevant_arg_0, ", "regex_for_relevant_arg_2, etc.]]
    # Wildcard * can be substituted for any single OSC address container, or any number of containers if it is the end of the pattern.
    # If only an argument's index is relevant, index 1 or the trigger response should be the relevant index.
    osc_trigger_response = []
    match target_type:
        case "channel_patch":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 2]
                case "fixture_manufacturer":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 3]
                case "fixture_model":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 4]
                case "address":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 5]
                case "address_of_intensity_parameter":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 6]
                case "current_level":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 7]
                case "osc_gel":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 8]
                case "text_1":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 9]
                case "text_2":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 10]
                case "text_3":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 11]
                case "text_4":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 12]
                case "text_5":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 13]
                case "text_6":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 14]
                case "text_7":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 15]
                case "text_8":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 16]
                case "text_9":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 17]
                case "text_10":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 18]
                case "part_count":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 19]
                case "notes":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/notes", 2]
        case "channel_part":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 2]
                case "fixture_manufacturer":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 3]
                case "fixture_model":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 4]
                case "address":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 5]
                case "address_of_intensity_parameter":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 6]
                case "current_level":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 7]
                case "osc_gel":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 8]
                case "text_1":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 9]
                case "text_2":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 10]
                case "text_3":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 11]
                case "text_4":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 12]
                case "text_5":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 13]
                case "text_6":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 14]
                case "text_7":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 15]
                case "text_8":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 16]
                case "text_9":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 17]
                case "text_10":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 18]
                case "part_count":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/list/*", 19]
                case "notes":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/%target_1%/notes", 2]
        case "channel":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/patch/%target_0%"
                    osc_trigger_response = ["/eos/out/get/patch/%target_0%/*/list/*", 2]
                case _:
                    # All other attributes associated with a channel
                    # Format the attribute as Eos expects it
                    attribute = attribute.replace("_", " ")
                    attribute = attribute.replace("\\", "/")
                    attribute = attribute.title()
                    attribute = "^%s [*" % attribute

                    osc_query_address_pattern = "/eos/user/0/newcmd/%target_0%/#"
                    osc_trigger_response = ["/eos/out/active/wheel/*=[%s]" % attribute, 2]
        case "cuelist":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 2]
                case "playback_mode":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 3]
                case "fader_mode":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 4]
                case "independent":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 5]
                case "htp":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 6]
                case "assert":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 7]
                case "block":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 8]
                case "background":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 9]
                case "solo_mode":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 10]
                case "timecode_list":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 11]
                case "oos_sync":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/list/*", 12]
                case "linked_cue_lists":
                    osc_query_address_pattern = "/eos/get/cuelist/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cuelist/%target_0%/*/links/list/*", 2]
        case "cue":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 2]
                case "up_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 3]
                case "up_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 4]
                case "down_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 5]
                case "down_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 6]
                case "focus_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 7]
                case "focus_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 8]
                case "color_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 9]
                case "color_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 10]
                case "beam_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 11]
                case "beam_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 12]
                case "preheat":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 13]
                case "curve":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 14]
                case "rate":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 15]
                case "mark":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 16]
                case "block":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 17]
                case "assert":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 18]
                case "link":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 19]
                case "follow_time":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 20]
                case "hang_time":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 21]
                case "all_fade":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 22]
                case "loop":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 23]
                case "solo":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 24]
                case "timecode":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 25]
                case "part_count":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 26]
                case "notes":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 27]
                case "scene":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 28]
                case "scene_end":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 29]
                case "cue_part_index":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/list/*", 30]
                case "effect_list":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/fx/list/*", 2]
                case "linked_cue_lists":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/links/list/*", 2]
                case "ext_link_action":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/*/actions/list/*", 2]
        case "cue_part":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 2]
                case "up_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 3]
                case "up_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 4]
                case "down_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 5]
                case "down_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 6]
                case "focus_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 7]
                case "focus_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 8]
                case "color_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 9]
                case "color_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 10]
                case "beam_time_duration":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 11]
                case "beam_time_delay":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 12]
                case "preheat":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 13]
                case "curve":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 14]
                case "rate":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 15]
                case "mark":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 16]
                case "block":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 17]
                case "assert":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 18]
                case "link":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 19]
                case "follow_time":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 20]
                case "hang_time":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 21]
                case "all_fade":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 22]
                case "loop":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 23]
                case "solo":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 24]
                case "timecode":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 25]
                case "part_count":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 26]
                case "notes":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 27]
                case "scene":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 28]
                case "scene_end":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 29]
                case "cue_part_index":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/list/*", 30]
                case "effect_list":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/fx/list/*", 2]
                case "linked_cue_lists":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/links/list/*", 2]
                case "ext_link_action":
                    osc_query_address_pattern = "/eos/get/cue/%target_0%/%target_1%/%target_2%"
                    osc_trigger_response = ["/eos/out/get/cue/%target_0%/%target_1%/%target_2%/actions/list/*", 2]
        case "group":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/group/%target_0%"
                    osc_trigger_response = ["/eos/out/get/group/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/group/%target_0%"
                    osc_trigger_response = ["/eos/out/get/group/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/group/%target_0%"
                    osc_trigger_response = ["/eos/out/get/group/%target_0%/list/*", 2]
                case "channel_list":
                    osc_query_address_pattern = "/eos/get/group/%target_0%"
                    osc_trigger_response = ["/eos/out/get/group/%target_0%/channels/list/*", 2]
        case "macro":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/macro/%target_0%"
                    osc_trigger_response = ["/eos/out/get/macro/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/macro/%target_0%"
                    osc_trigger_response = ["/eos/out/get/macro/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/macro/%target_0%"
                    osc_trigger_response = ["/eos/out/get/macro/%target_0%/list/*", 2]
                case "mode":
                    osc_query_address_pattern = "/eos/get/macro/%target_0%"
                    osc_trigger_response = ["/eos/out/get/macro/%target_0%/list/*", 3]
                case "command_text":
                    osc_query_address_pattern = "/eos/get/macro/%target_0%"
                    osc_trigger_response = ["/eos/out/get/macro/%target_0%/text/list/*", 2]
        case "sub":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 2]
                case "mode":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 3]
                case "fader_mode":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 4]
                case "htp":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 5]
                case "exclusive":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 6]
                case "background":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 7]
                case "restore":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 8]
                case "priority":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 9]
                case "up_time":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 10]
                case "dwell_time":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 11]
                case "down_time":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/list/*", 12]
                case "effect_list":
                    osc_query_address_pattern = "/eos/get/sub/%target_0%"
                    osc_trigger_response = ["/eos/out/get/sub/%target_0%/fx/list/*", 2]
        case "preset":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/preset/%target_0%"
                    osc_trigger_response = ["/eos/out/get/preset/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/preset/%target_0%"
                    osc_trigger_response = ["/eos/out/get/preset/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/preset/%target_0%"
                    osc_trigger_response = ["/eos/out/get/preset/%target_0%/list/*", 2]
                case "absolute":
                    osc_query_address_pattern = "/eos/get/preset/%target_0%"
                    osc_trigger_response = ["/eos/out/get/preset/%target_0%/list/*", 3]
                case "locked":
                    osc_query_address_pattern = "/eos/get/preset/%target_0%"
                    osc_trigger_response = ["/eos/out/get/preset/%target_0%/list/*", 4]
                case "channel_list":
                    osc_query_address_pattern = "/eos/get/preset/%target_0%"
                    osc_trigger_response = ["/eos/out/get/preset/%target_0%/channels/list/*", 2]
                case "by_type_channel_list":
                    osc_query_address_pattern = "/eos/get/preset/%target_0%"
                    osc_trigger_response = ["/eos/out/get/preset/%target_0%/byType/list/*", 2]
                case "effect_list":
                    osc_query_address_pattern = "/eos/get/preset/%target_0%"
                    osc_trigger_response = ["/eos/out/get/preset/%target_0%/fx/list/*", 2]
        case "ip":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/ip/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ip/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/ip/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ip/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/ip/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ip/%target_0%/list/*", 2]
                case "absolute":
                    osc_query_address_pattern = "/eos/get/ip/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ip/%target_0%/list/*", 3]
                case "locked":
                    osc_query_address_pattern = "/eos/get/ip/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ip/%target_0%/list/*", 4]
                case "channel_list":
                    osc_query_address_pattern = "/eos/get/ip/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ip/%target_0%/channels/list/*", 2]
                case "by_type_channel_list":
                    osc_query_address_pattern = "/eos/get/ip/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ip/%target_0%/byType/list/*", 2]
        case "cp":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/cp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cp/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/cp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cp/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/cp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cp/%target_0%/list/*", 2]
                case "absolute":
                    osc_query_address_pattern = "/eos/get/cp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cp/%target_0%/list/*", 3]
                case "locked":
                    osc_query_address_pattern = "/eos/get/cp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cp/%target_0%/list/*", 4]
                case "channel_list":
                    osc_query_address_pattern = "/eos/get/cp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cp/%target_0%/channels/list/*", 2]
                case "by_type_channel_list":
                    osc_query_address_pattern = "/eos/get/cp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/cp/%target_0%/byType/list/*", 2]
        case "fp":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/fp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fp/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/fp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fp/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/fp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fp/%target_0%/list/*", 2]
                case "absolute":
                    osc_query_address_pattern = "/eos/get/fp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fp/%target_0%/list/*", 3]
                case "locked":
                    osc_query_address_pattern = "/eos/get/fp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fp/%target_0%/list/*", 4]
                case "channel_list":
                    osc_query_address_pattern = "/eos/get/fp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fp/%target_0%/channels/list/*", 2]
                case "by_type_channel_list":
                    osc_query_address_pattern = "/eos/get/fp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fp/%target_0%/byType/list/*", 2]
        case "bp":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/bp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/bp/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/bp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/bp/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/bp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/bp/%target_0%/list/*", 2]
                case "absolute":
                    osc_query_address_pattern = "/eos/get/bp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/bp/%target_0%/list/*", 3]
                case "locked":
                    osc_query_address_pattern = "/eos/get/bp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/bp/%target_0%/list/*", 4]
                case "channel_list":
                    osc_query_address_pattern = "/eos/get/bp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/bp/%target_0%/channels/list/*", 2]
                case "by_type_channel_list":
                    osc_query_address_pattern = "/eos/get/bp/%target_0%"
                    osc_trigger_response = ["/eos/out/get/bp/%target_0%/byType/list/*", 2]
        case "curve":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/curve/%target_0%"
                    osc_trigger_response = ["/eos/out/get/curve/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/curve/%target_0%"
                    osc_trigger_response = ["/eos/out/get/curve/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/curve/%target_0%"
                    osc_trigger_response = ["/eos/out/get/curve/%target_0%/list/*", 2]
        case "effect":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/fx/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fx/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/fx/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fx/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/fx/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fx/%target_0%/list/*", 2]
                case "effect_type":
                    osc_query_address_pattern = "/eos/get/fx/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fx/%target_0%/list/*", 3]
                case "entry":
                    osc_query_address_pattern = "/eos/get/fx/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fx/%target_0%/list/*", 4]
                case "exit":
                    osc_query_address_pattern = "/eos/get/fx/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fx/%target_0%/list/*", 5]
                case "duration":
                    osc_query_address_pattern = "/eos/get/fx/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fx/%target_0%/list/*", 6]
                case "scale":
                    osc_query_address_pattern = "/eos/get/fx/%target_0%"
                    osc_trigger_response = ["/eos/out/get/fx/%target_0%/list/*", 7]
        case "snapshot":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/snap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/snap/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/snap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/snap/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/snap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/snap/%target_0%/list/*", 2]
        case "pixelmap":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 2]
                case "server_channel":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 3]
                case "interface":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 4]
                case "width":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 5]
                case "height":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 6]
                case "pixel_count":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 7]
                case "fixture_count":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/list/*", 8]
                case "layer_channel_list":
                    osc_query_address_pattern = "/eos/get/pixmap/%target_0%"
                    osc_trigger_response = ["/eos/out/get/pixmap/%target_0%/channels/list/*", 2]
        case "ms":
            match attribute:
                case "index":
                    osc_query_address_pattern = "/eos/get/ms/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ms/%target_0%/list/*", 0]
                case "uid":
                    osc_query_address_pattern = "/eos/get/ms/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ms/%target_0%/list/*", 1]
                case "label":
                    osc_query_address_pattern = "/eos/get/ms/%target_0%"
                    osc_trigger_response = ["/eos/out/get/ms/%target_0%/list/*", 2]

    raw_osc_query_address = osc_query_address_pattern
    raw_osc_trigger_response = osc_trigger_response

    final_osc_queries = []
    # Substitute in the target, and possibly attribute to get the final eos query and response
    for target in target_list:
        print(target_list, target)
        print(osc_trigger_response)
        final_osc_trigger_response = ["", raw_osc_trigger_response[1]]
        # Substitute in parts of the target. If any do not exist, the user gave the wrong information to complete the query, and it will not work as a result.
        # Target part 1
        try:
            final_osc_query_address_pattern = raw_osc_query_address.replace("%target_0%", target[0])
            final_osc_trigger_response[0] = raw_osc_trigger_response[0].replace("%target_0%", target[0])
        except IndexError:
            print("No target 0")
            final_osc_query_address_pattern = raw_osc_query_address
            final_osc_trigger_response[0] = raw_osc_trigger_response[0]

        # Target part 2
        try:
            final_osc_query_address_pattern = osc_query_address_pattern.replace("%target_1%", target[1])
            final_osc_trigger_response[0] = osc_trigger_response[0].replace("%target_1%", target[1])
        except IndexError:
            print("No target 1")
            pass

        # Target part 3
        try:
            final_osc_query_address_pattern = osc_query_address_pattern.replace("%target_2%", target[2])
            final_osc_trigger_response[0] = osc_trigger_response[0].replace("%target_2%", target[2])
        except IndexError:
            print("No target 2")
            pass

        final_osc_queries.append([final_osc_query_address_pattern, final_osc_trigger_response])

    print(final_osc_queries)
    return final_osc_queries



class EosQuery:
    """Holds all information related to a single Eos query."""

    def __init__(self, target_type, target, attribute, frame_type=None, frame_target=None):
        """Initialize with only information from the query"""
        frame_types = ["cue", "ip", "cp", "fp", "cp", "sub", "preset"]
        target_types = ["channel_patch", "channel", "channel_part", "cuelist", "cue", "cue_part", "group", "macro",
                        "sub", "preset", "ip", "cp", "fp", "bp", "curve", "effect", "snapshot", "pixelmap", "ms"]
        target_type_attributes = {"channel_patch": ["index", "uid", "label", "fixture_manufacturer", "fixture_model",
                                                    "address", "address_of_intensity_parameter", "current_level",
                                                    "osc_gel", "text_1", "text_2", "text_3", "text_4", "text_5",
                                                    "text_6", "text_7", "text_8", "text_9", "text_10", "part_count"],
                                  "channel_part": ["index", "uid", "label", "fixture_manufacturer", "fixture_model",
                                                   "address", "address_of_intensity_parameter", "current_level",
                                                   "osc_gel", "text_1", "text_2", "text_3", "text_4", "text_5",
                                                   "text_6", "text_7", "text_8", "text_9", "text_10", "part_count"],
                                  "cuelist": ["index", "uid", "label", "playback_mode", "fader_mode", "independent",
                                              "htp", "assert", "block", "background", "solo_mode", "timecode_list",
                                              "oos_sync", "linked_cue_lists"],
                                  "cue": ["index", "uid", "label", "up_time_duration", "up_time_delay",
                                          "down_time_duration", "down_time_delay", "focus_time_duration",
                                          "focus_time_delay", "color_time_duration", "color_time_delay",
                                          "beam_time_duration", "beam_time_delay", "preheat", "curve", "rate", "mark",
                                          "block", "assert", "link", "follow_time", "hang_time", "all_fade", "loop",
                                          "solo", "timecode", "part_count", "notes", "scene", "scene_end",
                                          "cue_part_index", "effect_list", "linked_cue_lists", "ext_link_action"],
                                  "cue_part": ["index", "uid", "label", "up_time_duration", "up_time_delay",
                                               "down_time_duration", "down_time_delay", "focus_time_duration",
                                               "focus_time_delay", "color_time_duration", "color_time_delay",
                                               "beam_time_duration", "beam_time_delay", "preheat", "curve", "rate",
                                               "mark", "block", "assert", "link", "follow_time", "hang_time",
                                               "all_fade", "loop", "solo", "timecode", "part_count", "notes", "scene",
                                               "scene_end", "cue_part_index", "effect_list", "linked_cue_lists",
                                               "ext_link_action"],
                                  "group": ["index", "uid", "label", "channel_list"],
                                  "macro": ["index", "uid", "label", "mode", "command_text"],
                                  "sub": ["index", "uid", "label", "mode", "fader_mode", "htp", "exclusive",
                                          "background", "restore", "priority", "up_time", "dwell_time", "down_time",
                                          "effect_list"],
                                  "preset": ["index", "uid", "label", "absolute", "locked", "channel_list",
                                             "by_type_channel_list", "effect_list"],
                                  "ip": ["index", "uid", "label", "absolute", "locked", "channel_list",
                                         "by_type_channel_list"],
                                  "cp": ["index", "uid", "label", "absolute", "locked", "channel_list",
                                         "by_type_channel_list"],
                                  "fp": ["index", "uid", "label", "absolute", "locked", "channel_list",
                                         "by_type_channel_list"],
                                  "bp": ["index", "uid", "label", "absolute", "locked", "channel_list",
                                         "by_type_channel_list"],
                                  "curve": ["index", "uid", "label"],
                                  "effect": ["index", "uid", "label", "effect_type", "entry", "exit", "duration",
                                             "scale"],
                                  "snapshot": ["index", "uid", "label"],
                                  "pixelmap": ["index", "uid", "label", "server_channel", "interface", "width",
                                               "height", "pixel_count", "fixture_count", "layer_channel_list"],
                                  "ms": ["index", "uid", "label"]}

        if frame_type is not None:
            if frame_type.lower() in frame_types:
                self.frame_type = frame_type.lower()
                self.frame_target = frame_target
            else:
                # Invalid frame type, disregard frame and frame target
                self.frame_type = None
                self.frame_target = None
        else:
            # No frame provided, disregard frame and frame target
            self.frame_type = None
            self.frame_target = None

        if target_type.lower() in target_types:
            self.target_type = target_type
            self.target = parse_multiple_targets(target)

            # Check that the attribute is valid for the target type. If target type is channel, hope for the best.
            if self.target_type == "channel" or (attribute in target_type_attributes[self.target_type]):
                self.attribute = attribute
            else:
                # Invalid attribute. This will invalidate the query, just have it query the UID.
                self.attribute = "uid"
        else:
            # Invalid target type, disregard target type, target, and attribute
            self.target_type = None
            self.target = None
            self.attribute = None

        # OSC addresses to send to set up the query
        self.setup_osc_commands = []
        
        # OSC addresses to obtain the requested information for the query
        self.main_address = ""
        self.main_args = []
        
        # OSC addresses to send to clean up after query information is received
        self.cleanup_osc_commands = []
        
        # OSC address pattern and argument which will contain query response when received.
        self.return_address = ""
        self.return_arg_index = 0
        
        # If the frame was of a valid type, determine the appropriate setup OSC messages to send
        # Else, leave setup_addresses blank
        self.setup_osc_commands = get_setup_osc(self.frame_type, self.frame_target)
        self.cleanup_osc_commands = get_cleanup_osc(self.frame_type, self.frame_target)
        
        # If the target type was valid, determine the OSC message and response to complete the query
        if target_type is not None:
            self.final_queries = get_query_osc(self.target_type, self.target, self.attribute)

            if self.final_queries is None:
                self.final_queries = []