from ansible.module_utils.basic import AnsibleModule
import requests



def add_node(node,check_mode):

    url = node.get("url")
    tag = node.get("tag")
    leader_url = node.get("leader_url")
    is_watcher = node.get("type") == "Watcher"

    if not leader_url:
        return {"changed": False, "msg": "Leader URL must be specified"}

    if not isinstance(tag, str) or not tag.isalnum() or tag != tag.upper():
        return {"changed": False, "msg": "Invalid tag: Node tag must be an uppercase non-empty alphanumeric string"}

    if not isinstance(url, str) or not url.startswith("http"):
        return {"changed": False, "msg": "Invalid URL: must be a valid HTTP(S) URL"}
    
    headers = {"Content-Type": "application/json"}

    if check_mode:
        return {"changed": True, "msg": f"Node {tag} would be added to the cluster"}
    try:
    
        add_url = f"{leader_url}/admin/cluster/node?url={url}&tag={tag}"
        if is_watcher:
            add_url += "&watcher=true"

        response = requests.put(add_url, headers=headers)
        response.raise_for_status()

    except requests.HTTPError as e:
        error_message = response.json().get("Message", response.text) if response.content else str(e)
        return {"changed": False, "msg": f"Failed to add node {tag}", "error": error_message}

    except requests.RequestException as e:
        return {"changed": False, "msg": f"Failed to add node {tag}", "error": str(e)}

    return {"changed": True, "msg": f"Node {tag} added to the cluster"}

def main():
    module_args = {
        "node": {"type": "dict", "required": True},
    }

    module = AnsibleModule(argument_spec=module_args, supports_check_mode=True)
    node = module.params["node"]

    try:
        changed,message = add_node(node, module.check_mode)
        module.exit_json(changed=changed, msg=message)

    except Exception as e:
        module.fail_json(msg=f"An error occurred: {str(e)}")


if __name__ == '__main__':
    main()
