"""Create blob containers and register the alerts, images and index datastores (issue #10).

Run from searchashouses/:  python azureml/setup/datastores.py
The containers live in the workspace's own storage account, so there is no new account and
no extra fixed cost: you only pay for the data stored. Safe to run again.

Access uses the storage account key. The script reads it at run time from the Azure
management API and hands it to Azure ML, which keeps it in the workspace key vault.
The key is never written to a file, printed or committed.
"""

from azure.ai.ml.entities import AccountKeyConfiguration, AzureBlobDatastore
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import BlobContainer
from azure_config import get_ml_client, load_settings

# datastore name (= container name) -> what it holds
DATASTORES = {
    "alerts": "Safety Gate alerts: raw pulls and the safetygate_alerts data asset",
    "listings": "Product listings: the abo_listings data asset (#16)",
    "images": "Product photos: ABO photo subset and alert images",
    "index": "FAISS index files built by build_index",
}


def main() -> None:
    settings = load_settings()
    group = settings["AZURE_RESOURCE_GROUP"]
    ml_client = get_ml_client()
    # The workspace stores its storage account as a full resource ID; the last part is the name.
    account = ml_client.workspaces.get(settings["AZUREML_WORKSPACE"]).storage_account.split("/")[-1]
    storage = StorageManagementClient(DefaultAzureCredential(), settings["AZURE_SUBSCRIPTION_ID"])
    # In azure-mgmt-storage 25 the result is dict-like, so `.keys` is the dict method;
    # the list of account keys is called `keys_property`.
    key = storage.storage_accounts.list_keys(group, account).keys_property[0].value

    for name, description in DATASTORES.items():
        try:
            storage.blob_containers.get(group, account, name)
            print(f"container {name}: exists")
        except ResourceNotFoundError:
            storage.blob_containers.create(group, account, name, BlobContainer())
            print(f"container {name}: created")
        datastore = AzureBlobDatastore(
            name=name,
            account_name=account,
            container_name=name,
            description=description,
            credentials=AccountKeyConfiguration(account_key=key),
        )
        ml_client.datastores.create_or_update(datastore)
        print(f"datastore {name}: registered")


if __name__ == "__main__":
    main()
