import React, { useState, useEffect } from 'react';
import { Flex, Divider, Alert, Button, message, Avatar } from 'antd';
import { CaretRightFilled, CloseOutlined, UserOutlined } from '@ant-design/icons';
import { Select, Typography, InputNumber, Space, Input, Card, Tooltip } from 'antd';
const { Text, Link } = Typography;
import { CopyToClipboard } from 'react-copy-to-clipboard';


const Home = ({ xhsUser, setXhsUser, dark }) => {
  const [messageApi, contextHolder] = message.useMessage();
  // 启动服务状态
  const [starting, setStarting] = useState(false);
  // 服务运行状态
  const [running, setRunning] = useState(false);
  // 端口
  const [port, setPort] = useState(parseInt(localStorage.getItem('config.port')) || 9999);
  // 路由
  const [endpoint, setEndpoint] = useState(localStorage.getItem('config.endpoint') || '/mcp');
  // 协议 shttp, sse
  const [proto, setProto] = useState(localStorage.getItem('config.proto') || 'sse');

  // 数据导出目录
  const [savePath, setSavePath] = useState(localStorage.getItem('config.savepath') || '');

  // mcp工具列表

  const [mcpTools, setMcpTools] = useState([]);

  const [isTest, setIsTest] = useState(!!localStorage.getItem('isTest'));
  const selectSavePath = async () => {
    if (typeof AppApi === 'undefined') {
      messageApi.error('未初始化API！')
      return console.error('未初始化AppApi');
    }
    const res = await AppApi.selectSavePath();
    if (res) {
      setSavePath(res);
      // 保存到缓存
      localStorage.setItem('config.savepath', res);
    }
  }
  // 只执行一次
  useEffect(() => {
    if (savePath == '') {
      AppApi.getDownloadPath().then(p => {
        setSavePath(p);
      });
    }
    getXhsUser();
  }, []);
  AppApi.getJoinedTest().then(r => {
    setIsTest(r);
  })

  // 获取xhs登陆用户
  // const [xhsUser, setXhsUser] = useState(null);
  const getXhsUser = async () => {
    if (typeof AppApi === 'undefined') {
      messageApi.error('未初始化API！')
      return console.error('未初始化AppApi');
    }
    const x = await AppApi.getXhsUserInfo();
    if (x) {
      console.log('xhsUser', x);
      setXhsUser(x);
      // 如果没有登陆，循环直到登陆成功
      // if (x.guest && running) return setTimeout(getXhsUser, 2000);
    }
    // if (x) {
    //   messageApi.success('已获取到小红书登陆用户：' + xhsUser);
    // } else {
    //   messageApi.warning('未获取到小红书登陆用户');
    // }
  }
  // get user
  // getXhsUser();

  // Get MCP tools list
  const getMcpTools = async () => {
    const tools = await AppApi.getMcpServerTools();
    console.log('mcptools:', tools)
    setMcpTools(tools);
  };

  // Start/stop MCP service
  const toggleServer = async (skipStop = false) => {
    if (typeof AppApi === 'undefined') {
      messageApi.error('API not initialized!')
      return console.error('AppApi not initialized');
    }
    if (!port || !endpoint) return messageApi.error('Please configure MCP port and route first!');
    if (!savePath) return messageApi.error('Please configure data export directory!');
    if (!endpoint.startsWith('/')) setEndpoint(`/${endpoint}`);
    setStarting(true);
    if (running && !skipStop) {
      try {
        const msg = await AppApi.stopMcpServer();
        messageApi.info(msg);
        setRunning(false);
        setStarting(false);
      } catch (err) {
        messageApi.warning(err);
        setStarting(false);
      }
      // AppApi.stopMcpServer().then(msg => {
      //   messageApi.info(msg);
      //   setRunning(false);
      //   setStarting(false);
      // }).catch(err => {
      //   messageApi.warning(err);
      //   setStarting(false);
      // })
    } else {
      try {
        const msg = await AppApi.startMcpServer({
          proto, port, endpoint, savePath
        });
        messageApi.success(msg);
        setRunning(true);
        setStarting(false);
        // 
        // get user
        getXhsUser();
        // 
        getMcpTools();
      } catch (err) {
        messageApi.warning(err);
        setStarting(false);
        setRunning(false);
      }
      // 存储配置到本地
      localStorage.setItem('config.port', port);
      localStorage.setItem('config.proto', proto);
      localStorage.setItem('config.endpoint', endpoint);
    }
  }

  const MCP_SERVER_LINK = `http://127.0.0.1:${port}${endpoint}`;
  return (
    <>
      {contextHolder}
      <Flex gap='middle' vertical>
        <Card title='Configuration' loading={starting} hoverable extra={
          <>
            {xhsUser && (
              <Tooltip title='Open Rednote Web'>
                <Button
                  size='small'
                  shape='round'
                  color={xhsUser.guest ? 'danger' : 'cyan'}
                  variant='solid'
                  onClick={() => {
                    window['AppApi'].toggleXhsBrowser();
                  }}
                  icon={xhsUser.guest ? <UserOutlined /> : <Avatar crossOrigin='anonymous' src={xhsUser.images || xhsUser.imageb} size={18} />}
                >{xhsUser.guest ? 'Login' : `Logged（${xhsUser.nickname}）`}</Button>
              </Tooltip>
            )}
            {xhsUser && <Divider type='vertical' />}
          <Tooltip title={running ? 'Stop' : 'Start'}>
            <Button onClick={() => toggleServer(false)} loading={starting} color={running ? 'danger' : 'primary'} variant='solid' shape='circle' icon={running ? <CloseOutlined /> : <CaretRightFilled />}></Button>
          </Tooltip>
          </>
        } styles={{
          body: {
            padding: 0
          }
        }}>
          <Alert banner message={(
            <>
              <Text>
                MCP Server{running ? ' is running.' : ' is stopped.'}
              </Text>
              {running && <Divider type='vertical' />}
              {running && (
                <Link>{MCP_SERVER_LINK}</Link>
              )}
            </>
          )} type={running ? 'success' : 'warning'} showIcon action={
            running && (
              <>
                {/* <Tooltip title='一键配置到Cherry Studio（测试版）'>
                  <Button disabled={!isTest} size='small' variant='filled' color='pink' onClick={() => {
                    const mcpJson = {
                      mcpServers: {
                        'xhs-mcp-server': {
                          name: 'xhs-mcp-server',
                          type: proto,
                          description: 'XiaoHongShu MCP-SERVER | aicu.icu',
                          isActive: true,
                          baseUrl: MCP_SERVER_LINK
                        }
                      }
                    };
                    const mcpJsonStr = JSON.stringify(mcpJson);
                    // --- 暂时关闭跳转cherry studio
                    console.log(mcpJsonStr)
                    const mcpJsonStrBase64 = btoa(mcpJsonStr);
                    const uri = `cherrystudio://mcp/install?servers=${mcpJsonStrBase64}`;
                    console.log(uri);
                    window.open(uri, '_blank');
                  }}>一键配置</Button>
                </Tooltip> */}
                <Divider type='vertical' />
                <CopyToClipboard text={MCP_SERVER_LINK} onCopy={(text, success) => {
                  messageApi.info(success ? 'Copied' : 'Error');
                }}>
                  <Tooltip title="Copy MCP Address">
                    <Button size='small' variant='filled' color='primary'>Copy</Button>
                  </Tooltip>
                </CopyToClipboard>
              </>
              )
          } />
          <Space style={{
            padding: 20
          }}>
            <Text>Transport</Text>
            <Tooltip title='MCP Transport Protocol'>
              <Select
                disabled={running}
                defaultValue={proto}
                placeholder="Select Protocol"
                style={{ width: 200 }}
                onChange={setProto}
                options={[
                  { value: 'shttp', label: 'Streamable HTTP' },
                  { value: 'sse', label: 'SSE' }
                ]}
              />
            </Tooltip>
            <Tooltip title='Port（1000-65535）'>
              <InputNumber placeholder='Port' disabled={running} min={1000} max={65535} defaultValue={port} onChange={setPort} />
            </Tooltip>
            <Tooltip title='Subpath of MCP Server'>
              <Input placeholder='Subpath' disabled={running} value={endpoint} onChange={e => {
                setEndpoint(e.target.value)
              }} />
            </Tooltip>
          </Space>
          <Space style={{
            padding: 20,
            paddingTop: 0
          }}>
            <Text>Data</Text>
            <Tooltip title='Data'>
              <Input placeholder='Data' value={savePath} readOnly style={{
                width: 345
              }} />
            </Tooltip>
            <Button onClick={selectSavePath} disabled={running}>...</Button>
          </Space>
        </Card>
    
      </Flex>
    </>
  )
}

export default Home;