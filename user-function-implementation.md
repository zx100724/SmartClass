# 4. 用户功能实现

## 4.1 系统架构与技术选型

本系统采用前后端分离架构，实现了完整的用户管理功能。后端基于Django和Django REST Framework构建，提供RESTful API接口；前端使用Vue 3和Element Plus框架，构建响应式用户界面。系统采用JWT（JSON Web Token）进行身份认证，确保API访问的安全性。

### 4.1.1 后端技术栈
- **框架**：Django 4.x
- **API框架**：Django REST Framework
- **认证机制**：JWT (JSON Web Token)
- **数据库**：SQLite (开发环境)

### 4.1.2 前端技术栈
- **框架**：Vue 3
- **UI库**：Element Plus
- **HTTP客户端**：Axios
- **路由**：Vue Router
- **状态管理**：localStorage (轻量级状态管理)

## 4.2 后端用户功能实现

### 4.2.1 用户模型

系统使用Django内置的`User`模型作为基础用户模型，并通过Django的`Group`模型实现用户角色管理。新注册用户默认被添加到"游客"用户组，后续可通过管理员进行角色调整。

### 4.2.2 API接口实现

#### 4.2.2.1 注册接口

注册接口处理用户注册请求，验证输入数据的有效性，并创建新用户。具体实现如下：

```python
@api_view(['POST'])
@permission_classes([AllowAny]) 
def register(request):
    """处理 Vue 前端的注册请求"""
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '') 

    if not username or not password:
        return Response({'error': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists():
        return Response({'error': '该用户名已被注册'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, password=password, email=email)
        visitor_group = Group.objects.get(name='游客')
        user.groups.add(visitor_group)
        return Response({
            'message': '注册成功',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

该接口首先验证用户名和密码是否为空，然后检查用户名是否已存在，最后创建新用户并将其添加到"游客"用户组。

#### 4.2.2.2 登录接口

登录接口使用Django REST Framework Simple JWT提供的`TokenObtainPairView`，验证用户凭据并返回JWT访问令牌：

```python
# 在 urls.py 中配置
path('api/login/', TokenObtainPairView.as_view(), name='login'),
```

#### 4.2.2.3 获取用户信息接口

获取用户信息接口返回当前登录用户的详细信息，包括用户名、邮箱、真实姓名和用户组：

```python
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    """获取当前登录用户的信息"""
    user = request.user
    group_name = user.groups.first().name if user.groups.exists() else "无分组"
    
    return Response({
        'username': user.username,
        'email': user.email,
        'real_name': user.first_name, 
        'group': group_name
    })
```

该接口使用`IsAuthenticated`权限装饰器，确保只有已认证用户才能访问。

#### 4.2.2.4 更新用户资料接口

更新用户资料接口允许用户修改个人信息，包括用户名、邮箱和真实姓名：

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """处理前端修改资料（账号、姓名、邮箱）的请求"""
    user = request.user
    data = request.data
    
    new_username = data.get('username', '').strip()
    new_email = data.get('email', '').strip()
    new_real_name = data.get('real_name', '').strip()

    if new_username and new_username != user.username:
        if User.objects.filter(username=new_username).exists():
            return Response({"error": "该用户名已被占用，请换一个"}, status=status.HTTP_400_BAD_REQUEST)
        user.username = new_username

    if 'email' in data:
        user.email = new_email
    if 'real_name' in data:
        user.first_name = new_real_name
        
    user.save()
    
    return Response({
        'status': 'success',
        'message': '个人资料更新成功！',
        'new_username': user.username
    })
```

该接口验证用户名是否已被占用，然后更新用户信息并返回成功响应。

#### 4.2.2.5 修改密码接口

修改密码接口允许用户更新登录密码：

```python
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """处理修改密码逻辑"""
    user = request.user
    new_pwd = request.data.get('new_password')
    
    if not new_pwd:
        return Response({'error': '密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_pwd)
    user.save()
    
    return Response({'message': '修改成功'})
```

该接口使用Django的`set_password`方法安全地更新密码，确保密码以哈希形式存储。

## 4.3 前端用户功能实现

### 4.3.1 登录组件

登录组件实现用户登录功能，包括表单验证、API调用和令牌存储：

```vue
const handleLogin = async () => {
  if (!loginForm.username || !loginForm.password) {
    ElMessage.warning('请填写用户名和密码')
    return
  }

  try {
    const response = await axios.post('http://127.0.0.1:8000/api/login/', {
      username: loginForm.username,
      password: loginForm.password
    })

    const token = response.data.access
    localStorage.setItem('token', response.data.access)
    localStorage.setItem('username', loginForm.username)

    ElMessage.success('登录成功！欢迎进入巡课系统')
    router.push('/dashboard')

  } catch (error) {
    console.error(error)
    ElMessage.error('登录失败：用户名或密码错误，或后端未启动')
  }
}
```

该组件验证输入字段，发送登录请求，存储JWT令牌，并在登录成功后跳转到仪表盘页面。

### 4.3.2 注册组件

注册组件实现用户注册功能，包括表单提交和错误处理：

```vue
const doRegister = async () => {
  try {
    const res = await axios.post('http://127.0.0.1:8000/api/register/', {
      username: username.value,
      password: password.value,
      email: email.value
    })
    
    ElMessage.success('注册成功！请登录')
    router.push('/login')
  } catch (err) {
    ElMessage.error('注册失败，用户名可能重复了')
  }
}
```

该组件发送注册请求，处理注册成功和失败的情况，并在注册成功后跳转到登录页面。

### 4.3.3 个人资料组件

个人资料组件实现用户资料管理功能，包括获取用户信息、更新资料和修改密码：

```vue
// 获取个人信息
const fetchUserInfo = async () => {
  try {
    const token = localStorage.getItem('token')
    if (!token) return router.push('/login')
    const res = await axios.get('http://localhost:8000/api/user-info/', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    userInfo.username = res.data.username
    userInfo.email = res.data.email
    userInfo.real_name = res.data.real_name || ''
    userGroup.value = res.data.group
  } catch (err) {
    ElMessage.error('身份验证失效或获取信息失败')
    if(err.response?.status === 401) router.push('/login')
  }
}

// 保存资料修改
const saveProfile = async () => {
  if (!userInfo.real_name.trim()) {
    ElMessage.warning('真实姓名不能为空！')
    return
  }

  saving.value = true
  try {
    const token = localStorage.getItem('token')
    await axios.post('http://localhost:8000/api/update-profile/', 
      { 
        email: userInfo.email,
        real_name: userInfo.real_name 
      }, 
      { headers: { 'Authorization': `Bearer ${token}` } }
    )
    ElMessage.success('个人资料更新成功')
  } catch (err) { 
    ElMessage.error(err.response?.data?.error || '资料更新失败') 
  } finally { 
    saving.value = false 
  }
}

// 修改密码
const handlePasswordChange = async () => {
  if (!passwordForm.newPassword) {
    ElMessage.warning('新密码不能为空')
    return
  }
  if (passwordForm.newPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致！')
    return
  }
  try {
    const token = localStorage.getItem('token')
    await axios.post('http://localhost:8000/api/change-password/', {
      new_password: passwordForm.newPassword
    }, { headers: { 'Authorization': `Bearer ${token}` } })
    
    ElMessageBox.alert('密码修改成功，请使用新密码重新登录系统', '安全提示', {
      confirmButtonText: '去登录',
      type: 'success',
      callback: () => { 
        localStorage.clear()
        router.push('/login')
      }
    })
  } catch (err) { 
    ElMessage.error('修改密码失败，请检查网络或联系管理员') 
  }
}
```

该组件实现了完整的用户资料管理功能，包括获取用户信息、验证输入、发送更新请求和处理错误情况。

### 4.3.4 路由守卫

路由守卫确保只有登录用户才能访问后台页面：

```javascript
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('access') || localStorage.getItem('token')
  
  if (to.path.startsWith('/dashboard') && !token) {
    next('/login')
  } else {
    next()
  }
})
```

该路由守卫在用户访问后台页面时检查是否存在有效的令牌，若不存在则重定向到登录页面。

## 4.4 用户功能交互流程

### 4.4.1 注册流程

1. **用户输入**：用户访问注册页面，输入用户名、密码和邮箱
2. **前端验证**：前端验证输入字段是否为空
3. **API调用**：前端发送注册请求到后端API
4. **后端处理**：后端验证用户名是否已存在，创建新用户并添加到"游客"组
5. **响应处理**：前端收到注册成功响应，跳转到登录页面

### 4.4.2 登录流程

1. **用户输入**：用户访问登录页面，输入用户名和密码
2. **前端验证**：前端验证输入字段是否为空
3. **API调用**：前端发送登录请求到后端API
4. **后端处理**：后端验证用户凭据，返回JWT访问令牌
5. **令牌存储**：前端存储令牌到localStorage
6. **页面跳转**：前端跳转到仪表盘页面

### 4.4.3 个人资料管理流程

1. **页面访问**：用户访问个人资料页面
2. **信息获取**：前端发送请求获取用户信息并显示
3. **用户修改**：用户修改个人资料或密码
4. **前端验证**：前端验证输入字段的有效性
5. **API调用**：前端发送更新请求到后端API
6. **后端处理**：后端更新用户信息，返回成功响应
7. **响应处理**：前端显示成功提示

### 4.4.4 异常处理

系统实现了完善的异常处理机制，包括：

1. **注册异常**：用户名已存在时返回错误信息
2. **登录异常**：用户名或密码错误时返回错误信息
3. **未授权访问**：未登录用户访问后台页面时重定向到登录页面
4. **令牌过期**：令牌过期或无效时返回401错误，前端跳转到登录页面
5. **网络错误**：网络连接失败时显示错误提示

## 4.5 技术实现要点

1. **认证机制**：使用JWT实现无状态会话管理，提高系统可扩展性
2. **权限控制**：使用Django REST Framework的权限装饰器控制接口访问权限
3. **前端状态管理**：使用localStorage存储用户令牌和基本信息，实现轻量级状态管理
4. **路由保护**：使用Vue Router的导航守卫确保只有登录用户才能访问后台页面
5. **错误处理**：前后端都实现了完善的错误处理机制，确保良好的用户体验
6. **数据验证**：前后端都对用户输入进行验证，确保数据完整性和安全性

## 4.6 代码优化建议

1. **前端API地址配置**：将API地址提取为配置项，避免硬编码，提高代码可维护性
2. **密码强度验证**：增加密码强度验证，提高系统安全性
3. **令牌刷新机制**：实现JWT令牌自动刷新，避免用户频繁登录
4. **表单验证增强**：使用Element Plus的表单验证规则，提供更详细的错误提示
5. **后端错误处理**：统一错误处理机制，返回更标准化的错误信息
6. **前端状态管理**：考虑使用Pinia或Vuex管理全局状态，提高代码可维护性

## 4.7 小结

本系统的用户功能实现采用了前后端分离架构，通过Django和Vue 3构建了完整的用户管理系统。系统实现了注册、登录、个人资料管理和密码修改等核心功能，使用JWT进行身份认证，确保API访问的安全性。

系统的实现遵循了现代Web应用开发的最佳实践，代码结构清晰，功能完善，用户体验良好。通过路由守卫和权限控制，确保了系统的安全性；通过完善的错误处理机制，提高了系统的可靠性。

同时，系统也存在一些可优化的空间，如API地址配置、密码强度验证、令牌刷新机制等，这些优化可以进一步提高系统的安全性和用户体验。