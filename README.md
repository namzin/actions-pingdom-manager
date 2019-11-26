# Github Actions: Pingdom Manager

This Github action can be used to automate the update/creation of Pingdom health checks
based on the contents of a YAML file in a Github repository.

#### Required Parameters

* FILENAME
            
  The location of the YAML file to parse relative to the GITHUB_WORKSPACE root

* API_KEY

  The Pingdom API key to use (this must have read/write access and will need to be 
  pre-configured via the Pingdom website)
      
#### Example Usage

The following example shows how the action can be used in a Github workflow file.

```yaml
name: Pingdom Manager Example

on:
  push:
    branches:
      - master

jobs:
  deploy-pingdom-health-checks:
    name: Deploy Pingdom Health Checks
    runs-on: ubuntu-latest
    steps:
      - name: Deploy Health Checks
        uses: eonx-com/actions-pingdom-manager@v1.0
        with:
          FILENAME: 'example.yaml'
          API_KEY: ${{ secrets.PINGDOM_API_KEY }}
```
