# azureml/schedules

Azure ML schedules: `monthly_retrain.yml` runs the training pipeline once a month (#78). Every run spends credit.

Create: `az ml schedule create -f azureml/schedules/monthly_retrain.yml`. Commands run from `searchashouses/`.
