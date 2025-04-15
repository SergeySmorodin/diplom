useEffect(() => {
  const fetchData = async () => {
    try {
      const responseData = await apiRequest('get', `project/${pk}`, {});
      setProjectData(responseData.data);
    } catch (error) {
      // Если ошибка пришла от сервера (например, 400/403/500)
      if (error.response) {
        const { data } = error.response;
        
        // Если есть общее сообщение (например, "message": "Ошибка")
        if (data.message) {
          setErrorMessage(data.message);
        } 
        // Если это ошибки валидации (например, {"username": ["Ошибка"]})
        else {
          // Собираем все ошибки в одну строку
          const errorMessages = Object.values(data).flat().join(' ');
          setErrorMessage(errorMessages);
        }
      } 
      // Если ошибка сети или другая ошибка
      else {
        setErrorMessage("Ошибка соединения с сервером");
      }
    }
  };
  fetchData();
}, []);