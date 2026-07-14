export interface SecurityAlert {
  timestamp: string;
  sourceIp: string;
  destIp?: string;
  attackType: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  protocol?: string;
  confScore?: number;
  actionTaken?: 'ISOLATE' | 'REVIEW' | 'IGNORE';
}

export interface SystemLog {
  timestamp: string;
  severity: string;
  module: string;
  message: string;
  status: string;
  color: string;
}

export interface ActiveConnection {
  sourceIp: string;
  destIp: string;
  protocol: string;
  load: number;
}

export interface TopologyNode {
  id: string;
  label: string;
  type: 'Internal' | 'External' | 'Gateway' | 'Threat' | 'Server';
  activeConnections: number;
  trafficRate: string;
  x: number;
  y: number;
  vx?: number;
  vy?: number;
}

export interface ReportItem {
  id: string;
  name: string;
  type: 'Audit' | 'Intelligence' | 'Vulnerability';
  generated: string;
  status: 'Ready' | 'Processing';
  hash: string;
}
