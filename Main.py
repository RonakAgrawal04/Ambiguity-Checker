import streamlit as st

def remove_left_recursion(productions):
    non_recursive = {}
    recursive = {}
    
    for non_terminal, rules in productions.items():
        non_recursive[non_terminal] = []
        recursive[non_terminal] = []
        for rule in rules:
            if rule[0] == non_terminal:
                recursive[non_terminal].append(rule[1:])
            else:
                non_recursive[non_terminal].append(rule)
    
    new_productions = {}
    
    for non_terminal in productions.keys():
        if recursive[non_terminal]:
            new_non_terminal = non_terminal + "'"
            new_productions[non_terminal] = [rule + new_non_terminal for rule in non_recursive[non_terminal]]
            new_productions[new_non_terminal] = [rule + new_non_terminal for rule in recursive[non_terminal]] + ['ε']
        else:
            new_productions[non_terminal] = non_recursive[non_terminal]
    
    return new_productions

def left_factoring(productions):
    factored_productions = {}
    
    for non_terminal, rules in productions.items():
        common_prefix = None
        for rule in rules:
            if common_prefix is None:
                common_prefix = rule
            else:
                for i, (a, b) in enumerate(zip(common_prefix, rule)):
                    if a != b:
                        common_prefix = common_prefix[:i]
                        break
        if common_prefix and common_prefix != rules[0]:
            new_non_terminal = non_terminal + "'"
            new_rule = common_prefix
            new_factored_rules = [rule[len(common_prefix):] for rule in rules if rule.startswith(common_prefix)]
            factored_productions[non_terminal] = [new_rule + new_non_terminal]
            factored_productions[new_non_terminal] = new_factored_rules + ['ε']
        else:
            factored_productions[non_terminal] = rules
    
    return factored_productions

def eliminate_ambiguity(productions, precedence, associativity):
    unambiguous_productions = {}
    operators = list(precedence.keys())

    def generate_precedence_rules(non_terminal, rules):
        terms = [rule for rule in rules if len(rule) == 1]
        ops = [rule for rule in rules if len(rule) > 1 and rule[1] in operators]
        levels = sorted(set(precedence[op[1]] for op in ops)) 
        last_non_terminal = non_terminal

        for level in levels[::-1]:  # Start from the highest precedence
            current_non_terminal = last_non_terminal + f"_{level}"
            level_rules = [op for op in ops if precedence[op[1]] == level]
            left_assoc = [f"{last_non_terminal}{op[1]}{current_non_terminal}" for op in level_rules if associativity[op[1]] == "left"]
            right_assoc = [f"{current_non_terminal}{op[1]}{last_non_terminal}" for op in level_rules if associativity[op[1]] == "right"]

            unambiguous_productions[current_non_terminal] = terms + left_assoc + right_assoc
            last_non_terminal = current_non_terminal

        return last_non_terminal

    for non_terminal, rules in productions.items():
        if any(rule[1:] for rule in rules if rule[1:] in operators):
            unambiguous_productions[non_terminal] = [generate_precedence_rules(non_terminal,rules)]
    return unambiguous_productions


def check_ambiguity(productions):
    for non_terminal, rules in productions.items():
        for rule in rules:
            cnt = 0
            for i in range(0, len(rule)):
                if non_terminal == rule[i]:
                    cnt += 1
            if cnt >= 2:
                return True
    return False

def format_productions(productions):
    formatted_productions = ""
    for non_terminal, rules in productions.items():
        formatted_productions += f"{non_terminal} -> " + " | ".join(rules) + "\n"
    return formatted_productions

st.title('Context-Free Grammar Analysis')

st.subheader("Enter Grammar Productions")
grammar_input = st.text_area("Enter grammar productions (one per line in the form 'A -> B'):")

process_button = st.button('Process Grammar')

if process_button:
    if grammar_input:
        productions = {}
        
        for line in grammar_input.strip().split('\n'):
            line = line.strip()
            if '->' in line:
                left, right = line.split('->')
                left = left.strip()
                right = right.strip().split('|')
                if left not in productions:
                    productions[left] = []
                productions[left].extend([r.strip() for r in right])
            else:
                st.write(f"Skipping malformed line: {line}")
        
        new_productions_lr = remove_left_recursion(productions)
        st.session_state.new_productions_lr = new_productions_lr
        new_productions_lf = left_factoring(new_productions_lr)
        st.session_state.new_productions_lf = new_productions_lf
        
        st.session_state.grammar_processed = True
        st.session_state.is_ambiguous = check_ambiguity(productions)

if st.session_state.get("grammar_processed"):
    st.subheader("Grammar After Removing Left Recursion")
    st.text(format_productions(st.session_state.new_productions_lr))
    st.subheader("Grammar After Left Factoring")
    st.text(format_productions(st.session_state.new_productions_lf))
    if st.session_state.is_ambiguous:
        st.subheader("Ambiguity Detection")
        st.write("The grammar is ambiguous. Please specify operator precedence and associativity.")

        precedence_input = st.text_area(
            "Enter precedence as 'operator1 > operator2 > ...':",
            value=st.session_state.get("precedence_input", "")
        )
        associativity_input = st.text_area(
            "Enter associativity as 'operator1:left, operator2:right, ...':",
            value=st.session_state.get("associativity_input", "")
        )

        if precedence_input and associativity_input:
            st.session_state.precedence_input = precedence_input
            st.session_state.associativity_input = associativity_input

            precedence = {op.strip(): i for i, op in enumerate(precedence_input.split('>'))}
            associativity = dict(item.strip().split(':') for item in associativity_input.split(','))

            new_productions_amb = eliminate_ambiguity(st.session_state.new_productions_lf, precedence, associativity)
            st.subheader("Grammar After Eliminating Ambiguity")
            st.text(format_productions(new_productions_amb))
    else:
        st.write("The grammar is not ambiguous.")
