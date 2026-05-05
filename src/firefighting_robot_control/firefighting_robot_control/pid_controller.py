import rclpy #type: ignore
from rclpy.node import Node #type: ignore
from geometry_msgs.msg import Twist #type: ignore
from nav_msgs.msg import Odometry #type: ignore
import math

class PIDController(Node):
    def __init__(self):
        super().__init__('pid_controller')
        
        # Publishers and Subscribers
        self.cmd_vel_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        from std_msgs.msg import Float64MultiArray #type: ignore
        from sensor_msgs.msg import JointState #type: ignore
        
        self.nozzle_cmd_pub = self.create_publisher(Float64MultiArray, '/nozzle_velocity_controller/commands', 10)
        self.joint_state_sub = self.create_subscription(JointState, '/joint_states', self.joint_state_callback, 10)

        # Target Configuration for Driving (Drive 2.0 meters straight)
        self.target_distance = 2.0  
        self.start_x = None
        self.start_y = None
        
        # Target Configuration for Nozzle (Aim to 0.5 radians up)
        self.target_nozzle_angle = 0.5
        
        # PID Constants for Driving
        self.kp_drive = 1.5
        self.ki_drive = 0.0
        self.kd_drive = 0.5
        
        # PID Constants for Nozzle Aiming
        self.kp_aim = 2.0
        self.ki_aim = 0.0
        self.kd_aim = 0.1
        
        # State variables for Driving
        self.prev_error_drive = 0.0
        self.integral_drive = 0.0
        self.current_distance = 0.0

        # State variables for Aiming
        self.prev_error_aim = 0.0
        self.integral_aim = 0.0

        self.get_logger().info("PID Controller Node Started! Aiming for 2.0 meters distance and 0.5 rad nozzle angle.")

    def odom_callback(self, msg):
        current_x = msg.pose.pose.position.x
        current_y = msg.pose.pose.position.y
        
        if self.start_y is None:
            self.start_x = current_x
            self.start_y = current_y
            return
            
        # Calculate Euclidean distance traveled
        self.current_distance = math.sqrt((current_x - self.start_x)**2 + (current_y - self.start_y)**2)
        
        # Calculate Error
        error = self.target_distance - self.current_distance
        
        # Stop condition
        if error < 0.05:
            self.stop_robot()
            return

        # PID Math
        self.integral_drive += error
        derivative = error - self.prev_error_drive
        
        # Compute control output (velocity)
        control_output = (self.kp_drive * error) + (self.ki_drive * self.integral_drive) + (self.kd_drive * derivative)
        
        # Clamp velocity to max 0.8 m/s
        control_output = max(min(control_output, 0.8), -0.8)
        
        # Create Twist message
        twist = Twist()
        twist.linear.x = control_output
        
        # Publish
        self.cmd_vel_pub.publish(twist)
        
        # Update state
        self.prev_error_drive = error
        
        self.get_logger().info(f"[Drive] Dist: {self.current_distance:.2f}m/{self.target_distance}m | Vel: {control_output:.2f}")

    def joint_state_callback(self, msg):
        try:
            # Find the index of the nozzle joint
            idx = msg.name.index('Revolute 5')
            current_angle = msg.position[idx]
        except ValueError:
            return # Joint not found yet

        # Calculate Error
        error = self.target_nozzle_angle - current_angle
        
        # Stop condition
        if abs(error) < 0.02:
            self.stop_nozzle()
            return

        # PID Math
        self.integral_aim += error
        derivative = error - self.prev_error_aim
        
        # Compute control output (velocity)
        control_output = (self.kp_aim * error) + (self.ki_aim * self.integral_aim) + (self.kd_aim * derivative)
        
        # Clamp velocity
        control_output = max(min(control_output, 1.0), -1.0)
        
        # Publish
        from std_msgs.msg import Float64MultiArray #type: ignore
        cmd_msg = Float64MultiArray()
        cmd_msg.data = [control_output]
        self.nozzle_cmd_pub.publish(cmd_msg)
        
        # Update state
        self.prev_error_aim = error

    def stop_robot(self):
        twist = Twist()
        twist.linear.x = 0.0
        self.cmd_vel_pub.publish(twist)

    def stop_nozzle(self):
        from std_msgs.msg import Float64MultiArray #type: ignore
        cmd_msg = Float64MultiArray()
        cmd_msg.data = [0.0]
        self.nozzle_cmd_pub.publish(cmd_msg)

def main(args=None):
    rclpy.init(args=args)
    node = PIDController()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.stop_robot()
        pass
        
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
